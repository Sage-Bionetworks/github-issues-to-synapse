# AWS Lambda - Github issues to Synapse
Write open Github issues to a Synapse table using AWS Lambda.

## Getting started

A few things that you need:

1. A Github API key
2. The username and API key for a Synapse account.
3. An AWS account

## Usage

1. Clone this repository.
2. Create a Python virtual environment `virtualenv`.
3. Install dependencies (`pip install -r requirements.txt`).

This currently requires to have the Synapse Python client built from source specifically from the following branch:

```
https://github.com/Sage-Bionetworks/synapsePythonClient/tree/SYNPY-553
```

The Synapse client currently requires access to `multiprocessing.dummy.Pool` for handling a multipart upload. AWS Lambda does not have the required shared memory mount point (`/dev/shm`) that this requires. This branch implements a workaround that should be temporary.

Also of note, AWS Lambda functions do not have write access to a user's home directory. The Lambda script changes the location of the Synapse cache:

```
synapseclient.cache.CACHE_ROOT_DIR = '/tmp/synapsecache/'
```

4. From the repository directory, use the following to create the Lambda code as a `.zip` file:

```
export REPODIR=`pwd`
pushd ${VIRTUAL_ENV}/lib/python2.7/site-packages/
zip ${REPODIR}/lambda-code.zip `find .`
popd
zip -r ${REPODIR}/lambda-code.zip ${REPODIR}/export_repo_issues_to_synapse.py
```

5. Upload to an Amazon S3 bucket:

```
aws s3 cp lambda-code.zip s3://my-bucket-for-lambda
```

6. Create a Lambda function (best practice is to use an IAM role specifically for this task):

```
aws lambda create-function --region us-east-1 --function-name IssuesToSynapse --code S3Bucket=my-bucket-for-lambda,S3Key=lambda-code.zip,S3ObjectVersion=1 --role arn:aws:iam::510534517075:role/MyLambdaRole --handler export_repo_issues_to_synapse.issues_to_table_handler --runtime python2.7 --timeout 100 --memory-size 512
```

From the AWS console, the function needs to have environment variables set for the:

1. Github API key (`GITHUB_API_KEY`)
1. Synapse username (`SYNAPSE_USERNAME`)
1. Synapse API key (`SYNAPSE_API_KEY`)

## Updating the function

Modifications to the code require re-creating the zip file, uploading to the S3 bucket, and then updating the Lambda function:


```
aws lambda update-function-code --function-name IssuesToSynapse --s3-bucket my-bucket-for-lambda --s3-key export_repo_issues_to_synapse.zip
```

## Creating the Synapse table

A Synapse table that uses the following column IDs is required to exist:

```
['1415', '4372', '60818', '60819', '60852', '60853', '61041']
```

## Triggering the function

The Lambda function requires an event of the following format:

```
 { "table_id": "syn123456", "repo": "myusername/myreponame"}
```

Where the `table_id` is the same as the one created above, and the `repo` is the repository from which to get the issues.

The Lambda function can be triggered by issue events from Github. Set up an SNS or SQS integration for the repository you want to watch. Note that you need to add `issue` events to the hook manually - see this [API documentation page](https://developer.github.com/v3/repos/hooks/#edit-a-hook) for how to edit a hook.
