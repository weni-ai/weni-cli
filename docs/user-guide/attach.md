# Attach a channel identity

`weni attach` links one channel identity (URN) to a consumer. You pass the URN and the anchor. The CLI does not look up the conversation, compare names, or call a model.

```bash
weni attach \
  --urn-id 42 \
  --anchor-type commerce_user_id \
  --anchor-value store-user-42 \
  --verified
```

`--anchor-type` is one of `commerce_user_id`, `verified_email`, or `tax_document`. Without `--verified`, the anchor is only claimed and histories stay separate.

The project is the one selected with `weni project use`, or the UUID passed in `--project-id`. The request goes to the Flows identity API. When that host differs from the CLI API, set `WENI_FLOWS_BASE_URL`.

A successful call prints JSON with `consumer_id`, `attachment_status`, and `affected_protocol_ids`. A refusal prints JSON with `error` set to `validation`, `conflicting_consumer`, `forbidden`, or `identity_unavailable`.
