# First Concrete Lean Certification

This is an authored governance example and an implementation check, not a
research outcome or evidence of a complete formally verified simulator.

- `request.json` is the published cycle/override request.
- `response.json` was freshly produced by actual SWI-Prolog 9.2.9 via PySwip
  0.3.3 in WSL during this step.
- `GovernanceCertificate.lean` is a readable translation plus the concrete
  kernel-checked `Conforms` proof and ballot/voter corollaries.
- `certification.json` is the actual command receipt: input/source/proof hashes,
  Lean 4.19.0, source fingerprints, axiom report and excluded claims.
- `checks.json` records executed regression/native checks and artifact hashes.

The generated `.olean` binary is retained locally by the command and its hash
is in the receipt. It is not checked into this evidence directory; rebuild the
readable source with the pinned toolchain or rerun the command into a new output
directory. Compiler artifacts can depend on toolchain/platform details.

```bash
pcds certify-governance --request docs/evidence/2026-10-15/lean_certification/request.json --response docs/evidence/2026-10-15/lean_certification/response.json --output-dir results/rebuilt-lean-certificate
python -m pytest -q -m lean tests/integration
```

The concrete proof reports the standard Lean axiom `propext`; it does not use
`sorry`, a custom axiom, or `native_decide`. JSON/schema validation, hashing and
literal translation remain trusted. The proof concerns the translated input and
claim, rather than backend identity, arbitrary runtime executions, physics or
empirical validity. See [the certification guide](../../../lean_certification.md).

The Lean tests also prove acceptance of eight rule/electorate cases and rejection
of 15 altered witnesses. The CLI rejects a forged winner without issuing a
successful receipt. The earlier build evidence had an empty-default-target gap;
the current check explicitly compiles `Wasteland` and checks that its governance
module exists. Historical records are retained without changing their claims.
