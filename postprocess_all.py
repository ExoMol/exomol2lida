from config.config import OUTPUT_DIR
from exomol2lida.exceptions import DatasetPostProcessorError
from process_all import postprocess_molecule

if __name__ == "__main__":
    for mol_output_path in OUTPUT_DIR.glob("*"):
        mol_formula = mol_output_path.name
        try:
            postprocess_molecule(mol_formula)
        except DatasetPostProcessorError as e:
            print(f"{mol_formula} POST-PROCESSING ABORTED: {type(e).__name__}: {e}")
        print()
