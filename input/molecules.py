data = {
  "CO": {
    "mol_slug": "CO",
    "iso_slug": "12C-16O",
    "dataset_name": "Li2015",
    "resolve_vib": ["v"]
  },
  "NO": {
    "mol_slug": "NO",
    "iso_slug": "14N-16O",
    "dataset_name": "XABC",
    "states_header": [
      "i", "E", "g_tot", "J", "dE", "tau", "g_J", "+/-", "e/f", "State", "v", "Lambda",
      "Sigma", "Omega", "label", "E_duo"
    ],
    "resolve_el": ["State"],
    "resolve_vib": ["v"]
  },
  "HF": {
    "mol_slug": "HF",
    "iso_slug": "1H-19F",
    "dataset_name": "Coxon-Hajig",
    "resolve_vib": ["v"]
  },
  "HCN": {
    "mol_slug": "HCN",
    "iso_slug": "1H-12C-14N",
    "dataset_name": "Harris",
    "resolve_vib": ["v1", "v2", "v3"],
    "only_with": {"iso":  "0"}
  },
  "HNC": {
    "mol_slug": "HCN",
    "iso_slug": "1H-12C-14N",
    "dataset_name": "Harris",
    "resolve_vib": ["v1", "v2", "v3"],
    "only_with": {"iso":  "1"}
  },
  "CS": {
    "mol_slug": "CS",
    "iso_slug": "12C-32S",
    "dataset_name": "JnK",
    "resolve_vib": ["v"]
  },
  "H2": {
    "mol_slug": "H2",
    "iso_slug": "1H2",
    "dataset_name": "RACPPK",
    "states_header": ["i", "E", "g_tot", "J", "v"],
    "resolve_vib": ["v"]
  },
  "LiH": {
    "mol_slug": "LiH",
    "iso_slug": "7Li-1H",
    "dataset_name": "CLT",
    "states_header": ["i", "E", "g_tot", "J", "v"],
    "resolve_vib": ["v"]
  },
  "SiH": {
    "mol_slug": "SiH",
    "iso_slug": "28Si-1H",
    "dataset_name": "SiGHTLY",
    "states_header": [
      "i", "E", "g_tot", "J", "tau", "g_factor", "+/-", "e/f", "State", "v", "Lambda",
      "Sigma", "Omega"
    ],
    "resolve_el": ["State"],
    "resolve_vib": ["v"],
    "mapping_el": {
      ("a4Sigma",): "a(4SIGMA-)",
      ("B2Sigma",): "B(2SIGMA-)",
    },
  },
  "NaH": {
    "mol_slug": "NaH",
    "iso_slug": "23Na-1H",
    "dataset_name": "Rivlin",
    "resolve_el": ["X/A"],
    "resolve_vib": ["v"],
    "mapping_el": {
      ("X",): "X(1SIGMA+)",
      ("A",): "A(1SIGMA+)"
    }
  },
  "MgH": {
    "mol_slug": "MgH",
    "iso_slug": "24Mg-1H",
    "dataset_name": "Yadin",
    "resolve_vib": ["v"]
  },
  "SiO": {
    "mol_slug": "SiO",
    "iso_slug": "28Si-16O",
    "dataset_name": "EBJT",
    "resolve_vib": ["v"]
  },
  "H3+": {
    "mol_slug": "H3_p",
    "iso_slug": "1H3_p",
    "dataset_name": "MiZATeP",
    "states_header": [
      "i", "E", "g_tot", "J", "tau", "p", "Sym", "v1", "v2", "l2", "G", "U", "K"
    ],
    "resolve_vib": ["v1", "v2"]
  },
  "CN": {
    "mol_slug": "CN",
    "iso_slug": "12C-14N",
    "dataset_name": "Trihybrid",
    "states_header": [
      "i", "E", "g_tot", "J", "unc", "tau", "g", "+/-", "e/f", "State", "v", "Lambda",
      "Sigma", "Omega", "Source", "E_Duo"
    ],
    "resolve_el": ["State"],
    "resolve_vib": ["v"],
    "mapping_el": {
      ("X",): "X(2SIGMA+)",
      ("A",): "A(2PI)",
      ("B",): "B(2SIGMA+)"
    }
  },
  "NaCl": {
    "mol_slug": "NaCl",
    "iso_slug": "23Na-35Cl",
    "dataset_name": "Barton",
    "resolve_vib": ["v"]
  },
  "VO": {
    "mol_slug": "VO",
    "iso_slug": "51V-16O",
    "dataset_name": "VOMYT",
    "states_header": [
      "i", "E", "g_tot", "J", "tau", "+/-", "e/f", "State", "v", "Lambda", "Sigma",
      "Omega"
    ],
    "resolve_el": ["State"],
    "resolve_vib": ["v"],
    "only_without": {"State": "0"},
    "mapping_el": {
      ("b2Gamma",): "b(2GAMMA)",
      ("X",): "X(4SIGMA-)",
      ("a2",): "a(2SIGMA-)",
      ("Ap",): "A'(4PHI)",
      ("A",): "A(4PI)",
      ("b2",): "b(2GAMMA)",
      ("c2",): "c(2DELTA)",
      ("d2",): "d(2SIGMA+)",
      ("B",): "B(4PI)",
      ("e2",): "e(2PHI)",
      ("C",): "C(4SIGMA-)",
      ("f2",): "f(2PI)",
      ("D",): "D(4DELTA)",
      ("g2",): "g(2PI)",
    },
  },
  "SH": {
    "mol_slug": "SH",
    "iso_slug": "32S-1H",
    "dataset_name": "GYT",
    "states_header": [
      "i", "E", "g_tot", "J", "tau", "g-factor", "parity", "e/f", "State", "v",
      "Lambda", "Sigma", "Omega"
    ],
    "resolve_el": ["State"],
    "resolve_vib": ["v"]
  },
  "ScH": {
    "mol_slug": "ScH",
    "iso_slug": "45Sc-1H",
    "dataset_name": "LYT",
    "resolve_el": ["State"],
    "resolve_vib": ["v"]
  },
  "KCl": {
    "mol_slug": "KCl",
    "iso_slug": "39K-35Cl",
    "dataset_name": "Barton",
    "resolve_vib": ["v"]
  },
  "CaO": {
    "mol_slug": "CaO",
    "iso_slug": "40Ca-16O",
    "dataset_name": "VBATHY",
    "states_header": [
      "i", "E", "g_tot", "J", "tau", "/-", "e/f", "State", "v", "Lambda", "Sigma",
      "Omega"
    ],
    "resolve_el": ["State"],
    "resolve_vib": ["v"]
  },
  "PN": {
    "mol_slug": "PN",
    "iso_slug": "31P-14N",
    "dataset_name": "YYLT",
    "resolve_vib": ["v"]
  },
  "PS": {
    "mol_slug": "PS",
    "iso_slug": "31P-32S",
    "dataset_name": "POPS",
    "states_header": [
      "i", "E", "g_tot", "J", "tau", "g_lande", "+/-", "e/f", "State", "v", "Lambda",
      "Sigma", "Omega"
    ],
    "resolve_el": ["State"],
    "resolve_vib": ["v"]
  },
  "PO": {
    "mol_slug": "PO",
    "iso_slug": "31P-16O",
    "dataset_name": "POPS",
    "states_header": [
      "i", "E", "g_tot", "J", "tau", "g_lande", "+/-", "e/f", "State", "v", "Lambda",
      "Sigma", "Omega"
    ],
    "resolve_vib": ["v"]
  },
  "NS": {
    "mol_slug": "NS",
    "iso_slug": "14N-32S",
    "dataset_name": "SNaSH",
    "states_header": [
      "i", "E", "g_tot", "J", "tau", "g_lande", "+/-", "e/f", "State", "v", "Lambda",
      "Sigma", "Omega"
    ],
    "resolve_vib": ["v"]
  },
  "SiS": {
    "mol_slug": "SiS",
    "iso_slug": "28Si-32S",
    "dataset_name": "UCTY",
    "resolve_vib": ["v"]
  },
  "PH": {
    "mol_slug": "PH",
    "iso_slug": "31P-1H",
    "dataset_name": "LaTY",
    "states_header": [
      "i", "E", "g_tot", "J", "g_lande", "+/-", "e/f", "State", "v", "N"
    ],
    "resolve_el": ["State"],
    "resolve_vib": ["v"]
  },
  "SiH2": {
    "mol_slug": "SiH2",
    "iso_slug": "28Si-1H2",
    "dataset_name": "CATS",
    "states_header": [
      "i", "E", "g_tot", "J", "Gamma", "v1", "v2", "v3", "Gamma_vib", "Ka", "Kc",
      "Gamma_rot", "Ci", "n1", "n2", "n3"
    ],
    "resolve_vib": ["v1", "v2", "v3"]
  }
}
