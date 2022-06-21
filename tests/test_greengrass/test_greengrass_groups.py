import boto3
from botocore.exceptions import ClientError
import freezegun
import pytest

from moto import mock_greengrass
from moto.core import get_account_id
from moto.settings import TEST_SERVER_MODE

ACCOUNT_ID = get_account_id()


@freezegun.freeze_time("2022-06-01 12:00:00")
@mock_greengrass
def test_create_group():

    client = boto3.client("greengrass", region_name="ap-northeast-1")
    init_core_ver = {
        "Cores": [
            {
                "CertificateArn": f"arn:aws:iot:ap-northeast-1:{ACCOUNT_ID}:cert/36ed61be9c6271ae8da174e29d0e033c06af149d7b21672f3800fe322044554d",
                "Id": "123456789",
                "ThingArn": f"arn:aws:iot:ap-northeast-1:{ACCOUNT_ID}:thing/CoreThing",
            }
        ]
    }

    create_core_def_res = client.create_core_definition(
        InitialVersion=init_core_ver, Name="TestCore"
    )
    core_def_ver_arn = create_core_def_res["LatestVersionArn"]

    init_grp = {"CoreDefinitionVersionArn": core_def_ver_arn}

    grp_name = "TestGroup"
    create_grp_res = client.create_group(Name=grp_name, InitialVersion=init_grp)
    create_grp_res.should.have.key("Arn")
    create_grp_res.should.have.key("Id")
    create_grp_res.should.have.key("LastUpdatedTimestamp")
    create_grp_res.should.have.key("LatestVersion")
    create_grp_res.should.have.key("LatestVersionArn")
    create_grp_res.should.have.key("Name").equals(grp_name)
    create_grp_res["ResponseMetadata"]["HTTPStatusCode"].should.equal(201)

    if not TEST_SERVER_MODE:
        create_grp_res.should.have.key("CreationTimestamp").equals(
            "2022-06-01T12:00:00.000Z"
        )
        create_grp_res.should.have.key("LastUpdatedTimestamp").equals(
            "2022-06-01T12:00:00.000Z"
        )


@freezegun.freeze_time("2022-06-01 12:00:00")
@mock_greengrass
def test_create_group_version():

    client = boto3.client("greengrass", region_name="ap-northeast-1")
    create_grp_res = client.create_group(Name="TestGroup")
    group_id = create_grp_res["Id"]

    group_ver_res = client.create_group_version(GroupId=group_id)
    group_ver_res.should.have.key("Arn")
    group_ver_res.should.have.key("CreationTimestamp")
    group_ver_res.should.have.key("Id").equals(group_id)
    group_ver_res.should.have.key("Version")

    if not TEST_SERVER_MODE:
        group_ver_res["CreationTimestamp"].should.equal("2022-06-01T12:00:00.000Z")


@mock_greengrass
def test_create_group_version_with_invalid_id():

    client = boto3.client("greengrass", region_name="ap-northeast-1")
    with pytest.raises(ClientError) as ex:
        client.create_group_version(GroupId="cd2ea6dc-6634-4e89-8441-8003500435f9")

    ex.value.response["Error"]["Message"].should.equal("That group does not exist.")
    ex.value.response["Error"]["Code"].should.equal("IdNotFoundException")


@pytest.mark.parametrize(
    "def_ver_key_name,arn,error_message",
    [
        (
            "CoreDefinitionVersionArn",
            "123",
            "Cores definition reference does not exist",
        ),
        (
            "CoreDefinitionVersionArn",
            "arn:aws:greengrass:ap-northeast-1:944137583148:/greengrass/definition/cores/fc3b3e5b-f1ce-4639-88d3-3ad897d95b2a/versions/dd0f800c-246c-4973-82cf-45b109cbd99b",
            "Cores definition reference does not exist",
        ),
        (
            "DeviceDefinitionVersionArn",
            "123",
            "Devices definition reference does not exist",
        ),
        (
            "DeviceDefinitionVersionArn",
            "arn:aws:greengrass:ap-northeast-1:944137583148:/greengrass/definition/devices/fc3b3e5b-f1ce-4639-88d3-3ad897d95b2a/versions/dd0f800c-246c-4973-82cf-45b109cbd99b",
            "Devices definition reference does not exist",
        ),
        (
            "FunctionDefinitionVersionArn",
            "123",
            "Lambda definition reference does not exist",
        ),
        (
            "FunctionDefinitionVersionArn",
            "arn:aws:greengrass:ap-northeast-1:944137583148:/greengrass/definition/functions/fc3b3e5b-f1ce-4639-88d3-3ad897d95b2a/versions/dd0f800c-246c-4973-82cf-45b109cbd99b",
            "Lambda definition reference does not exist",
        ),
        (
            "ResourceDefinitionVersionArn",
            "123",
            "Resource definition reference does not exist",
        ),
        (
            "ResourceDefinitionVersionArn",
            "arn:aws:greengrass:ap-northeast-1:944137583148:/greengrass/definition/resources/fc3b3e5b-f1ce-4639-88d3-3ad897d95b2a/versions/dd0f800c-246c-4973-82cf-45b109cbd99b",
            "Resource definition reference does not exist",
        ),
        (
            "SubscriptionDefinitionVersionArn",
            "123",
            "Subscription definition reference does not exist",
        ),
        (
            "SubscriptionDefinitionVersionArn",
            "arn:aws:greengrass:ap-northeast-1:944137583148:/greengrass/definition/subscriptions/fc3b3e5b-f1ce-4639-88d3-3ad897d95b2a/versions/dd0f800c-246c-4973-82cf-45b109cbd99b",
            "Subscription definition reference does not exist",
        ),
    ],
)
@mock_greengrass
def test_create_group_version_with_invalid_version_arn(
    def_ver_key_name, arn, error_message
):

    client = boto3.client("greengrass", region_name="ap-northeast-1")
    create_grp_res = client.create_group(Name="TestGroup")
    group_id = create_grp_res["Id"]

    definition_versions = {def_ver_key_name: arn}

    with pytest.raises(ClientError) as ex:
        client.create_group_version(GroupId=group_id, **definition_versions)

    ex.value.response["Error"]["Message"].should.equal(
        f"The group is invalid or corrupted. (ErrorDetails: [{error_message}])"
    )
    ex.value.response["Error"]["Code"].should.equal("400")
