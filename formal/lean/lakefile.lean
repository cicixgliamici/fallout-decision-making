import Lake
-- Lake supplies Lean's build system; its DSL declares the package and library.
open Lake DSL

package wasteland where
  -- Build the actual proof library by default; an empty target set proves nothing.

@[default_target]
lean_lib Wasteland where
  -- Resolve module paths from formal/lean: Wasteland.Governance corresponds
  -- to Wasteland/Governance.lean. Dependencies are local to this small package.
  srcDir := "."
