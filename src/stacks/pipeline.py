import aws_cdk

from aws_cdk import (
    App,
    Stack,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    aws_ssm as ssm,
)


class Pipeline(Stack):
    def __init__(self, app: App, id: str, props, **kwargs) -> None:
        super().__init__(app, id, **kwargs)

        # Define the s3 artifact
        source_output = codepipeline.Artifact(artifact_name='source')

        # Create the pipeline specifications
        pipeline = codepipeline.Pipeline(
            self,
            "Pipeline",
            pipeline_name=props['namespace'],
            artifact_bucket=props['pipeline_bucket'],
            stages=[
                codepipeline.StageProps(
                    stage_name='Source',
                    actions=[
                        codepipeline_actions.S3SourceAction(
                            bucket=props['pipeline_bucket'],
                            bucket_key='source.zip',
                            action_name='S3Source',
                            run_order=1,
                            output=source_output,
                            trigger=codepipeline_actions.S3Trigger.POLL
                        ),
                    ]
                ),
                codepipeline.StageProps(
                    stage_name='Build',
                    actions=[
                        codepipeline_actions.CodeBuildAction(
                            action_name='DockerBuildImages',
                            input=source_output,
                            project=props['cb_docker_build'],
                            run_order=1,
                        )
                    ]
                )
            ]
        )

        # Give the Pipelines IAM roel permissions to read/write to the bucket
        props['pipeline_bucket'].grant_read_write(pipeline.role)

        # Create an SSM string to get the pipelines name
        pipeline_param = ssm.StringParameter(
            self,
            "EndeavourCorePipelineName",
            parameter_name=f"{props['namespace']}-pipeline",
            string_value=pipeline.pipeline_name,
            description='cdk pipeline',
        )

        aws_cdk.CfnOutput(
            self,
            "PipelineName",
            description="Pipeline",
            value=pipeline.pipeline_name
        )
