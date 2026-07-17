# Client cryptographic prototype

Task 12 is a required predecessor of encrypted messaging. Its implementation is
client-only: the server continues to store public keys and opaque encrypted
envelopes, and no server package imports a private-key operation.

## Version 1 constructions

Identity profiles use independent raw X25519 encryption and Ed25519 signing key
pairs. Keys start at version 1 and rotate monotonically by purpose. Public-key
fingerprints use the shared SHA-256 canonical fingerprint function. Private keys
are serialised as 32 raw bytes, encrypted using AES-256-GCM with a fresh 96-bit
nonce and authenticated key metadata, and written atomically to a per-profile
JSON store. The 256-bit unlock key is supplied from the existing operating-system
secure-store boundary. Locking drops parsed handles and overwrites the mutable
unlock-key buffer where Python permits; the implementation does not claim perfect
memory erasure.

Each message version receives a fresh 256-bit AES-GCM content key and 96-bit
nonce. The message AAD binds protocol version, identifiers, sender, type, reply,
timestamp, version, attachment identifiers and algorithm. Every recipient,
including the sender, receives a separate envelope made with a fresh ephemeral
X25519 key, HKDF-SHA-256, and AES-256-GCM. Ciphertext includes the standard
128-bit authentication tag. An Ed25519 signature covers the AAD, ciphertext,
nonce, signing-key version, algorithm, and a canonical SHA-256 digest of every
recipient envelope. Recipients verify the signature before unwrapping or
decrypting anything.

Local records derive purpose-separated AES keys with HKDF for private keys,
message cache, offline queue and search-index purposes. Attachment files are
processed in bounded chunks. Each chunk uses AES-GCM with a nonce consisting of
an 8-byte random prefix and a 4-byte chunk index; its AAD binds protocol version,
index and plaintext size. The encrypted stream stores a four-byte ciphertext
length followed by ciphertext with its appended tag. Plaintext and ciphertext
SHA-256 hashes are maintained incrementally, and incomplete output is removed.

## Failure and trust behavior

Invalid signatures, GCM tags, key records, contexts, checksums, key lengths or
formats produce safe typed failures and never return plaintext. Public keys are
still distributed by the server in Version 1, so a malicious server could
substitute a key before independent fingerprint comparison. Stable fingerprints,
version history and key-change events make that limitation visible; they do not
turn the server into an independent trust authority.

The initial offline queue contains ciphertext-only requests in memory. Durable,
encrypted local persistence belongs to the later client-database stage; no
plaintext queue is written in this stage.

## Verification map

`tests/unit/client/test_task_12_crypto.py` covers key generation, encrypted
storage, lock/reload, wrong-key and tamper rejection, message round trips,
signature/ciphertext tampering, purpose separation, bounded attachment streaming,
hash validation and cancellation cleanup.

