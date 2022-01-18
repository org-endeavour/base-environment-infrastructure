import aws_cdk

from aws_cdk import (
    App,
    Stack,
    aws_s3 as s3,
    aws_ecr as ecr,
    aws_codebuild as codebuild,
    aws_ssm as ssm,
)


class Base(Stack):
    def __init__(self, app: App, id: str, props, **kwargs) -> None:
        super().__init__(app, id, **kwargs)

        # The S3 Bucket used by the core CodePipeline 
        pipeline_bucket = s3.Bucket(
            self,
            "PipelineSourceBucket",
            bucket_name=f"{props['namespace'].lower()}-{aws_cdk.Aws.ACCOUNT_ID}",
            versioned=True,
            removal_policy=aws_cdk.RemovalPolicy.DESTROY)

        # SSM parameter to get bucket name later
        bucket_param = ssm.StringParameter(
            self,
            "EndeavourCorePipelineSourceBucketName",
            parameter_name=f"{props['namespace']}-bucket",
            string_value=pipeline_bucket.bucket_name,
            description='cdk pipeline bucket',
        )

        # ECR Repo for core environment docker images
        ecr_repo = ecr.Repository(
            self,
            "endeavour",
            repository_name=f"{props['namespace']}",
            removal_policy=aws_cdk.RemovalPolicy.DESTROY
        )

        # CodeBuild project to run in pipeline
        cb_docker_build = codebuild.PipelineProject(
            self,
            "DockerBuild",
            project_name=f"{props['namespace']}-Docker-Build",
            build_spec=codebuild.BuildSpec.from_source_filename(
                filename='pipeline_delivery/docker_build_buildspec.yml'),
            environment=codebuild.BuildEnvironment(
                privileged=True,
            ),
            # pass the ECR repo URI into the codebuild project so codebuild knows where to push
            environment_variables={
                'ecr': codebuild.BuildEnvironmentVariable(
                    value=ecr_repo.repository_uri),
                'tag': codebuild.BuildEnvironmentVariable(
                    value='cdk')
            },
            description='Pipeline for CodeBuild',
            timeout=aws_cdk.Duration.minutes(60),
        )

        # CodeBuild IAM permissions to read/write to the CodePipeline source bucket
        pipeline_bucket.grant_read_write(cb_docker_build)

        # CodeBuild IAM permissions to interact with ECR
        ecr_repo.grant_pull_push(cb_docker_build)

        aws_cdk.CfnOutput(
            self,
            "ECRURI",
            description="ECR URI",
            value=ecr_repo.repository_uri,
        )
        aws_cdk.CfnOutput(
            self,
            "S3Bucket",
            description="S3 Bucket",
            value=pipeline_bucket.bucket_name
        )

        self.output_props = props.copy()
        self.output_props['pipeline_bucket'] = pipeline_bucket
        self.output_props['cb_docker_build'] = cb_docker_build

    # pass objects to another stack
    @property
    def outputs(self):
        return self.output_props
