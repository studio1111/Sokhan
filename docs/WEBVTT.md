# WebVTT compatibility

The parser supports standard WEBVTT headers, optional cue identifiers, timestamps with or without an hour field, cue settings, and NOTE/STYLE/REGION metadata blocks. The serializer emits normalized timestamps and cue identifiers. Styling and region metadata are intentionally not copied to translated output.
