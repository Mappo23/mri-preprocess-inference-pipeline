from .steps.dldirect_predict import DLDirectPredict
from .steps.qc_roi import QCRoiStep

# Registry of steps
STEP_REGISTRY = {
    "dldirect": DLDirectPredict,
    "qc_roi": QCRoiStep,
}


class Pipeline:
    def __init__(self, config):
        self.steps = []

        for step_cfg in config["pipeline"]:
            # Expect each step to have a "type" key
            step_type = step_cfg["type"]
            params = step_cfg.get("params", {})

            if step_type not in STEP_REGISTRY:
                raise KeyError(f"Unknown pipeline step: {step_type}")

            print(f">>> Instantiating step: {step_type}")
            self.steps.append(STEP_REGISTRY[step_type](params))

    def run(self, ctx):
        for step in self.steps:
            ctx = step.run(ctx)
        return ctx