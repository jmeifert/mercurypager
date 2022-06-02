# mercury-pager
Mercury Pager, Because POCSAG is so 80s.

Make sure to configure POP and IMAP in mercury.conf. Send page emails as plaintext.

pager-server.py listens for pages with IMAP and sends them over radio.

pager-rx.py listens for pages on the default audio input device.