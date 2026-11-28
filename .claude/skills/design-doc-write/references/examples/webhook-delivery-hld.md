# Webhook Delivery Service — High-Level Design

**Status:** Draft

> **Note:** Invented example. It shows the shape, pacing and decision pattern of an HLD; the system, figures and names are fictional.

Integrators will get every webhook within five minutes of the event, even through a short endpoint outage, and a slow endpoint will stop delaying everyone else's. This doc covers how events turn into deliveries, how each endpoint is rate limited, and what happens to an endpoint that stays down. We need approval of the retry ceiling listed under Open items.

**Not covered here:** producing events and the event schema (the Event Bus HLD); the integrator dashboard (the Dashboard HLD).

## Glossary

- **Integrator** — a customer who registers an HTTPS endpoint to receive event notifications.
- **Endpoint** — one integrator URL, with its signing secret and rate limit.
- **Delivery** — one attempt to POST one event to one endpoint.
- **Dead-letter store** — where an event goes after its last retry fails; kept 14 days for replay.

## Background

The event bus calls each integrator's endpoint inline, from the worker that produced the event. A slow endpoint holds that worker for the full 30-second timeout. In last quarter's worst incident, one integrator's outage tied up 40 of 64 workers and delayed every other integrator's events by 22 minutes. Failed calls are logged and dropped; nothing retries them.

## 1. Overview

The webhook delivery service is a separate service that reads events from the bus and delivers them to each endpoint at the pace that endpoint can take. For an integrator the visible change is that deliveries arrive reliably and a failure is retried instead of lost.

One event, sent to two endpoints:

1. The bus publishes `invoice.paid`. The service writes one delivery per subscribed endpoint to the delivery queue.
2. Endpoint A returns `200` in 80 ms; its delivery is marked `DELIVERED`.
3. Endpoint B times out; its delivery is rescheduled for 30 seconds later. Endpoint A is not affected.
4. Endpoint B returns `200` on the second attempt; its delivery is marked `DELIVERED`.

Three facts shape the design: endpoints fail independently (section 2), each endpoint has a rate it can absorb (section 3), and some endpoints stay down for hours (section 4).

## 2. A slow endpoint delays only itself

Integrators receive their events on time whatever other integrators' endpoints are doing. Each endpoint gets its own queue partition and a small fixed number of in-flight slots.

| Property | Value | Reason |
|---|---|---|
| Partition key | endpoint id | A backlog stays inside the endpoint that caused it |
| In-flight slots per endpoint | 4 | Caps how much capacity one endpoint can hold |
| Request timeout | 10 seconds | The current 30 seconds is the main cause of worker starvation |

> **Endpoints never share a partition.** Two endpoints owned by the same integrator are isolated too, so one broken URL cannot hold up that integrator's working one.

Chose per-endpoint partitions over one shared queue with a per-endpoint concurrency cap; comparison in Appendix A.

## 3. Deliveries never exceed what an endpoint can absorb

Integrators running small servers stop receiving bursts they cannot handle. Each endpoint has a rate limit enforced by a token bucket that holds up to 20 tokens and refills at the endpoint's rate; a delivery spends one token.

| Setting | Default | Range |
|---|---|---|
| Rate | 10 deliveries per second | 1–100, set by the integrator |
| Burst | 20 deliveries | Fixed |

With the bucket empty, a delivery waits in its partition. It is neither dropped nor counted as a failed attempt.

## 4. Failed deliveries are retried, then parked

An integrator whose endpoint is down for a short time still receives every event. A delivery that fails with a timeout, a connection error, a `5xx` or a `429` is retried on this schedule:

| Attempt | Wait before it | Time since the event |
|---|---|---|
| 1 | — | 0 |
| 2 | 30 seconds | 30 seconds |
| 3 | 2 minutes | 2.5 minutes |
| 4 | 10 minutes | 12.5 minutes |
| 5 | 1 hour | about 1.2 hours |
| 6 | 6 hours | about 7.2 hours |

Any other `4xx` is not retried: the endpoint rejected the event, and sending it again will not change the answer. When the last attempt fails, the event moves to the dead-letter store, where the integrator can replay it from the dashboard for 14 days.

The dashboard shows one status per event across all its endpoints. One event sent to three endpoints:

- Two delivered and one on attempt 3: `PARTIAL`.
- The third then succeeds: `DELIVERED`.
- The third reaches the dead-letter store instead: `PARTIAL` until it is replayed.

## 5. Open items

| Item | State |
|---|---|
| Retry ceiling | Open. Six attempts over about 7 hours (section 4), or eight over about 24 hours. Recommended: six, since most outages in last quarter's incident log ended within four hours. |
| Signing-secret rotation | Open. Required before general availability; no mechanism designed yet. |
| Replay rate limit | Open. Whether a replay spends the endpoint's normal tokens or a separate allowance. |

## Appendices

## Appendix A — Decision register

How per-endpoint partitions compare with the alternatives.

| Option | For | Against | Outcome |
|---|---|---|---|
| Per-endpoint partitions | Isolation is structural; backlog visible per endpoint | More partitions to operate | Chosen: isolation is the reason the service exists |
| Shared queue, per-endpoint concurrency cap | One queue to operate | A stuck delivery at the head still delays those behind it | Rejected: a smaller version of today's failure |
| Worker pool per integrator | Easy to reason about | Two endpoints of one integrator still block each other | Rejected: breaks the section 2 rule |

## Appendix — Audience notes

| Field | Answer |
|---|---|
| **Readers** | Platform engineers who run the event bus (main); the security reviewer |
| **Prior knowledge** | HIGH on the event bus; LOW on how integrator endpoints behave and on retry trade-offs |
| **Takeaway** | Moving delivery into its own service, partitioned per endpoint, means one slow endpoint cannot delay anyone else |
| **Stakes** | Today one integrator's outage delays every integrator's events and pages the bus on-call |
| **Ask** | Approve the retry ceiling by the end of the month |
| **Expected questions** | Why not just lower the timeout? (section 2, Appendix A); what happens during a long outage? (section 4); does the event schema change? (Not covered here: no) |
