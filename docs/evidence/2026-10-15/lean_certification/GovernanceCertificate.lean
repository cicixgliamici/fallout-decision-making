import Wasteland.Governance

namespace GovernanceCertificate
open Wasteland Wasteland.Governance
set_option maxRecDepth 10000
set_option maxHeartbeats 2000000

def request : Request := {
  decisionId := "contract-example:cycle-and-override",
  requestHash := "209bee77997499833d17f14155b9e06e09e29430d9d86ae172fe2977bd7e9ef0",
  rule := .liquid_democracy,
  institutionalChecks := true,
  residents := [
    {
      name := "ada",
      role := .farmer,
      alive := true,
      sanctioned := false,
      ranking := [.farming, .medicine, .defense, .exploration]
    },
    {
      name := "bram",
      role := .farmer,
      alive := true,
      sanctioned := false,
      ranking := [.medicine, .farming, .defense, .exploration]
    },
    {
      name := "cleo",
      role := .farmer,
      alive := true,
      sanctioned := false,
      ranking := [.defense, .farming, .medicine, .exploration]
    },
    {
      name := "dax",
      role := .guard,
      alive := true,
      sanctioned := false,
      ranking := [.exploration, .farming, .medicine, .defense]
    }
  ],
  links := [
    {
      source := "ada",
      target := "bram",
      weight := {
        numerator := 3602879701896397,
        denominator := 4503599627370496
      }
    },
    {
      source := "ada",
      target := "cleo",
      weight := {
        numerator := 3602879701896397,
        denominator := 4503599627370496
      }
    },
    {
      source := "bram",
      target := "cleo",
      weight := {
        numerator := 1,
        denominator := 1
      }
    },
    {
      source := "cleo",
      target := "bram",
      weight := {
        numerator := 1,
        denominator := 1
      }
    },
    {
      source := "cleo",
      target := "dax",
      weight := {
        numerator := 3602879701896397,
        denominator := 4503599627370496
      }
    }
  ],
  food := {
    numerator := 100,
    denominator := 1
  },
  water := {
    numerator := 100,
    denominator := 1
  },
  medicine := {
    numerator := 50,
    denominator := 1
  },
  energy := {
    numerator := 2,
    denominator := 1
  },
  security := {
    numerator := 14,
    denominator := 1
  }
}

def claim : Claim := {
  requestHash := "209bee77997499833d17f14155b9e06e09e29430d9d86ae172fe2977bd7e9ef0",
  decision := {
    mandate := "vote",
    eligibleVoters := ["ada", "bram", "cleo", "dax"],
    representatives := [("ada", "ada"), ("bram", "bram"), ("cleo", "dax"), ("dax", "dax")],
    scores := [(.farming, 1), (.medicine, 1), (.defense, 0), (.exploration, 2)],
    votedPolicy := .exploration,
    selectedPolicy := .farming,
    permissionOverride := true
  },
  ballots := [
    {
      voter := "ada",
      topic := .farming,
      trace := {
        holder := "ada",
        path := ["ada", "bram", "cleo", "bram"],
        reason := "cycle"
      },
      votes := [.farming]
    },
    {
      voter := "bram",
      topic := .medicine,
      trace := {
        holder := "bram",
        path := ["bram"],
        reason := "no_eligible_expert"
      },
      votes := [.medicine]
    },
    {
      voter := "cleo",
      topic := .defense,
      trace := {
        holder := "dax",
        path := ["cleo", "dax"],
        reason := "no_eligible_expert"
      },
      votes := [.exploration]
    },
    {
      voter := "dax",
      topic := .exploration,
      trace := {
        holder := "dax",
        path := ["dax"],
        reason := "no_eligible_expert"
      },
      votes := [.exploration]
    }
  ],
  permissions := [
    {
      policy := .farming,
      allowed := true,
      reason := "unconditional"
    },
    {
      policy := .medicine,
      allowed := true,
      reason := "unconditional"
    },
    {
      policy := .defense,
      allowed := true,
      reason := "requirements_met"
    },
    {
      policy := .exploration,
      allowed := false,
      reason := "security_below_15"
    }
  ]
}

/-- Kernel-checked conformance of this concrete, translated witness. -/
theorem certificate_conforms : Conforms request claim := by decide

theorem original_ballots_conserved : claim.ballots.length = (electorate request).length :=
  accepted_ballot_count request claim certificate_conforms

theorem original_voters_preserved : claim.ballots.map (·.voter) =
    (electorate request).map (·.name) :=
  accepted_ballot_voters request claim certificate_conforms

#print axioms certificate_conforms
end GovernanceCertificate
