# Endpoint Pause — Mini-Design

**Status:** Draft

> **Note:** Invented example. It shows the shape of a mini-design; the feature and figures are fictional.

Integrators will be able to pause deliveries to one endpoint for planned maintenance and receive everything they missed when they resume. This doc covers the pause state, what happens to deliveries during a pause, and how long a pause can last. We would like comments on the 72-hour limit.

**Not covered here:** the delivery queue and retry schedule ([Webhook Delivery Service HLD](webhook-delivery-hld.md)).

## Background

An integrator doing maintenance today can only let deliveries fail. Every failure uses up a retry, so a four-hour window can push events into the dead-letter store and leave the integrator replaying them by hand.

## 1. Pausing holds deliveries without using retries

A pause is a flag on the endpoint that stops new delivery attempts without counting them as failures. While it is set, deliveries collect in the endpoint's partition.

| Action | Effect |
|---|---|
| Pause | No new attempts start; attempts already in flight finish |
| Resume | Held deliveries go out oldest first, at the endpoint's normal rate limit |
| Limit reached | The endpoint resumes by itself after 72 hours |

Example: an endpoint is paused at 09:00 and 12 events arrive before it resumes at 11:00. On resume it receives all 12 at its limit of 10 per second, finishing in just over a second.

Chose an automatic 72-hour limit over an open-ended pause, because a forgotten pause would let the queue grow with nobody noticing.

## 2. Open items

| Item | State |
|---|---|
| Pause limit | Open. 72 hours, or configurable up to 7 days. Recommended: 72 hours. |

## Appendices

## Appendix — Audience notes

| Field | Answer |
|---|---|
| **Readers** | Delivery service engineers (main); the integrator support lead |
| **Prior knowledge** | HIGH on the delivery service; MEDIUM on how integrators run maintenance |
| **Takeaway** | A pause holds deliveries without using retries, and ends on its own |
| **Stakes** | Planned maintenance currently causes dead-letter replays and support tickets |
| **Ask** | Comments on the 72-hour limit this week |
| **Expected questions** | What happens to attempts in flight? (section 1); why have a limit at all? (section 1) |
