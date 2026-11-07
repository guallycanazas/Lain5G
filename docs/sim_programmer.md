# Physical SIM programmer

OpenLain5G includes an optional local page for programming a supported physical
test USIM. It is independent of **Subscribers**: this workflow writes the card,
while the subscriber page later stores the matching IMSI, Ki, and OPc in the
selected packet core.

## Supported hardware and scope

- Through a PC/SC reader, the bridge detects **sysmoUSIM-SJS1**,
  **sysmoISIM-SJA2**, and **sysmoISIM-SJA5** by their pySim-recognized card
  profiles.
- This version writes only **sysmoUSIM-SJS1**. SJA2 and SJA5 are identified but
  remain read-only in this workflow until their profile-specific write and
  read-back verification are implemented. Their factory ICCID must be
  preserved. Unknown cards are reported without attempting writes.
- The card's ADM1 code is required. Do not guess it; failed ADM checks may lock
  card administration.
- Commercial operator SIMs, eSIM profiles, ISIM/CoIMS applets, OTA keys, SMSC,
  APN/DNN settings, and subscriber database changes are outside this page.
- The bridge runs only in application operations mode and is not given a host
  USB bus mount. It receives access only to the host PC/SC socket in that mode.
- The backend never logs the submitted Ki, OPc, or ADM1 and never returns the
  authentication keys. They remain in browser memory for the current page only.

## Host setup

Connect a compatible PC/SC reader. No host Python or pySim installation is
needed. The installer prepares the PC/SC service and CCID packages; operations
mode starts the bridge alongside the app:

```sh
./lain5g app start --operations --open
```

The installer enables PC/SC socket activation where available. The app startup
builds the bridge image if needed and starts its container with the web
application. No SIM programming occurs until the user submits and confirms a
card write in the web page.

The bridge uses `/run/pcscd/pcscd.comm` by default. Set
`LAIN5G_PCSC_SOCKET` in `.env.app` if the host uses another PC/SC socket path.
Use `./lain5g app status` and `./lain5g app logs` to inspect the full stack.
Stopping the application also stops the bridge.

## Programming flow

1. Select a PC/SC reader and inspect the inserted card. The bridge identifies
   known SJS1, SJA2, and SJA5 profiles. It reports other cards as unknown and
   refuses writes to models not enabled in this workflow.
2. Enter the network's MCC and MNC, an IMSI beginning with those values, and an
   ICCID with a valid check digit. Generate or enter a 128-bit Ki and OPc.
3. Enter the card's ADM1, acknowledge the physical write, then confirm the write
   dialog. The ADM1 field is cleared as soon as submission begins.
4. The bridge writes ICCID, Ki, OPc, IMSI, and MNC length, then reads the values
   back for verification. An interrupted write may leave a partial card; inspect
   it before retrying.
5. After success, save an optional encrypted credential file. Encryption is
   performed in the browser with PBKDF2-SHA-256 and AES-256-GCM; OpenLain5G does
  not store this file or its passphrase. The same page can decrypt and restore
  this file locally in the browser when needed.
6. Add the same subscriber credentials to the appropriate Open5GS core. The SIM
   page does not create a subscriber record automatically.

The encrypted backup uses a format-specific JSON envelope. Keep its passphrase
separately; if it is lost, the credentials cannot be recovered from OpenLain5G.

## API and implementation

- `GET /api/sim-programmer/status` reports whether the local bridge and readers
  are available without exposing card data.
- `POST /api/sim-programmer/inspect` checks one reader without writing.
- `POST /api/sim-programmer/program` is protected by the same local mutation
  setting used by other write operations. It accepts a narrow typed payload and
  returns only card identity and read-back field names.

The optional container is built from the pinned Osmocom pySim commit listed in
`images/sim-programmer/Dockerfile`; it is reachable only on the app's Docker
network and has no published host port. Its service accepts only reader-list,
card-inspection, and fixed card-programming requests, not arbitrary APDUs.
