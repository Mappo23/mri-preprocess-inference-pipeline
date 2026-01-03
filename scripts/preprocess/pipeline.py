from .steps.dcm2niix import Dcm2NiixStep
from .steps.reorient import ReorientStep
from .steps.resample import ResampleStep
from .steps.synthstrip import SynthStripStep
from .steps.qc import QCStep


STEP_REGISTRY = {
    "dcm2niix": Dcm2NiixStep,
    "reorient": ReorientStep,
    "resample": ResampleStep,
    "synthstrip": SynthStripStep,
    "qc": QCStep,
}

class Pipeline:
    def __init__(self, config):
        self.steps = []
        for step_cfg in config["pipeline"]:
            print(">>> Instantiating step:", step_cfg["type"])
            step_cls = STEP_REGISTRY[step_cfg["type"]]
            self.steps.append(step_cls(step_cfg.get("params")))

    def run(self, ctx):
        for step in self.steps:
            ctx = step.run(ctx)
        return ctx