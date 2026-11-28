Read this before you write or draft text that others read. It binds every
session that loads the worker contract.

# Writing for other readers

Issues, PR descriptions and replies, docs, messages and asks are read by
reviewers, collaborators and later maintainers, so `owner-talk.md`'s plain-terms
rule holds for them too.

- **Links.** Any issue, PR, review or doc you mention is a link on its own
  name, e.g. `[#482](https://github.com/acme/orders-service/pull/482)`: not a
  bare number, and not a URL next to the name. Take the URL from something you
  read, never a guess. In paste-ready text for chat or email, where markdown
  is lost, the full URL stands in place of the link.
- **Only what the reader can open.** A fact that lives only in a private
  working file is written out inline instead of linked.
- **No AI footer or sign-off** in a post or a paste-ready draft.
- **Edit pass.** Text for others longer than three sentences (an issue
  comment, a message, a PR reply, a draft under `asks/`) goes through
  `refining-technical-writing` in edit mode before you post or commit it.
  Design docs use the `design-doc-*` skills instead, and a PR description gets
  its pass inside `preparing-code-reviews`.
- **Asks to other people.** Something you need from another person or team is
  work, not an open item. Write the request ready to send (to whom, what, why,
  needed by when) as `<work root>/asks/ASK-<workstream>-<recipient>-<topic>.md`
  with `state: draft` as its first line, commit it, and list it under
  `Asks drafted:`. Sending it is the owner's job.
