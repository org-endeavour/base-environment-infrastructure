from aws_cdk import (
    App,
    Stack,
)

from stacks import (
    base,
    pipeline,
)

props = {
    'namespace': 'endeavour-infrastructure',
}

app = App()

base = base.Base(app, f"{props['namespace']}-base", props)

pipeline = pipeline.Pipeline(app, f"{props['namespace']}-pipeline", base.outputs)
pipeline.add_dependency(base)

app.synth()
