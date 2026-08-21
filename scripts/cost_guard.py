import boto3
from datetime import datetime, timezone
from botocore.exceptions import NoCredentialsError, ClientError

MAX_AGE_HOURS = 2

def get_age_hours(created_time):
    now = datetime.now(timezone.utc)
    age = now - created_time
    return round(age.total_seconds() / 3600, 2)

def check_eks_clusters(region):
    eks = boto3.client("eks", region_name=region)
    findings = []

    cluster_names = eks.list_clusters()["clusters"]

    for name in cluster_names:
        details = eks.describe_cluster(name=name)["cluster"]
        created_at = details["createdAt"]
        age = get_age_hours(created_at)

        findings.append({
            "type": "EKS Cluster",
            "name": name,
            "status": details["status"],
            "age_hours": age,
            "over_limit": age > MAX_AGE_HOURS,
        })

    return findings

def check_ec2_instances(region):
    ec2 = boto3.client("ec2", region_name=region)
    findings = []

    response = ec2.describe_instances(
        Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
    )

    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            launch_time = instance["LaunchTime"]
            age = get_age_hours(launch_time)
            instance_id = instance["InstanceId"]
            instance_type = instance["InstanceType"]

            findings.append({
                "type": "EC2 Instance",
                "name": instance_id,
                "status": f"{instance_type}, running",
                "age_hours": age,
                "over_limit": age > MAX_AGE_HOURS,
            })

    return findings

def main():
    region = "us-east-1"
    print(f"Checking AWS account for cost-incurring resources in {region}...\n")

    all_findings = []

    try:
        all_findings += check_eks_clusters(region)
        all_findings += check_ec2_instances(region)
    except NoCredentialsError:
        print("No AWS credentials found. Run 'aws configure' first.")
        return
    except ClientError as e:
        print(f"AWS API error: {e}")
        return

    if not all_findings:
        print("No cost-incurring resources found. You're clear.")
        return

    any_over_limit = False
    for item in all_findings:
        flag = "⚠️  OVER LIMIT" if item["over_limit"] else "OK"
        if item["over_limit"]:
            any_over_limit = True
        print(f"[{flag}] {item['type']}: {item['name']} | Status: {item['status']} | Age: {item['age_hours']}h")

    if any_over_limit:
        print("\n🚨 Some resources have exceeded the time limit. Consider running: eksctl delete cluster --name <your-cluster-name>")
if __name__ == "__main__":
    main()
