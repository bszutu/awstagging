# updated by Ben Szutu <bszutu AT gmail dot com>
# improvement to original script, add exception handling for instance with Ephemeral storage
# which does not have Id and cause original script to crash


import copy
import logging
import os
import boto3
import time

from_region = 'us-east-1'
to_region = 'us-west-2'
filter_key = 'tag:DeleteOn'
filter_value = ['11-21-2018']

logging.basicConfig(level=os.environ.get('LOG_LEVEL', 'INFO'))

ec2_from = boto3.client('ec2', region_name=from_region)
ec2_to = boto3.client('ec2', region_name=to_region)
logger = logging.getLogger(__name__)

def boto3_tag_list_to_ansible_dict(tags_list):
    tags_dict = {}
    for tag in tags_list:
        if 'key' in tag and not tag['key'].startswith('aws:'):
            tags_dict[tag['key']] = tag['value']
        elif 'Key' in tag and not tag['Key'].startswith('aws:'):
            tags_dict[tag['Key']] = tag['Value']

    return tags_dict

def ansible_dict_to_boto3_tag_list(tags_dict):
    tags_list = []
    for k, v in tags_dict.items():
        tags_list.append({'Key': k, 'Value': v})

    return tags_list

# this is where we tag things after it was created.
def tag_snapshots(AMI, tags):
    snapshots = {}
    # sleep in order for the snapshot to be at least assigned, so we can get SnapshotID for the EBS
    time.sleep(15)

    for image in ec2_to.describe_images(ImageIds=[AMI['ImageId']])['Images']:
        # print ('\nimage ====\n')
        # print (image)
        # to tag volumes, e.g., (1/3) (2/3) (3/3)
        devnum = 0
        numberofdevs=len(image['BlockDeviceMappings'])
        for device in image['BlockDeviceMappings']:
            # print ('\ndevice ====\n')
            # print (device)
            devnum += 1
            # here's where to set name for the snapshot
            tags['Name'] = 'SNAP-' + tags['Name'] + ' ' + device['DeviceName'] + ' (' + str(devnum) + '/' + str(numberofdevs) + ')'
            # print ('\ndevice-EBS ===\n' + str(devnum))
            # print (device['Ebs'])
            ec2_to.create_tags(Resources=[device['Ebs']['SnapshotId']], Tags=ansible_dict_to_boto3_tag_list(tags))


def copy_AMI():
    snapshots = {}

    for image in ec2_from.describe_images(Owners=['self'], Filters=[{'Name': filter_key, 'Values': filter_value}])['Images']:
        tags = boto3_tag_list_to_ansible_dict(image.get('Tags', []))
        # print (image)
        # to tag volumes, e.g., (1/3) (2/3) (3/3)
        tags = boto3_tag_list_to_ansible_dict(image.get('Tags', []))
        # print (tags)
        response = ec2_to.copy_image(
            Name=tags['Name'],
            SourceImageId=image["ImageId"],
            SourceRegion=from_region
        )
        # print (response)
        ec2_to.create_tags(
            Resources=[response['ImageId']], 
            Tags=ansible_dict_to_boto3_tag_list(tags)
        )
        # time.sleep(0)

        #tag the snapshot created with the AMI
        # print(AMIid)
        # tag_snapshots(response, tags)        
    #     numberofdevs=len(image['BlockDeviceMappings'])
    #     for device in image['BlockDeviceMappings']:
    #         try:
    #             if 'SnapshotId' in device['Ebs']:
    #                 devnum += 1
    #                 snapshot = snapshots[device['Ebs']['SnapshotId']]
    #                 snapshot['Used'] = True
    #                 cur_tags = boto3_tag_list_to_ansible_dict(snapshot.get('Tags', []))
    #                 new_tags = copy.deepcopy(cur_tags)
    #                 new_tags.update(tags)
    #                 new_tags['ImageId'] = image['ImageId']
    #                 # here's where to change formatting
    #                 new_tags['Name'] = 'AMI:' + image['Name'] + ' ' + device['DeviceName'] + ' (' + str(devnum) + '/' + str(numberofdevs) + ')'
    #                 if new_tags != cur_tags:
    #                     logger.info('{0}: Tags changed to {1}'.format(snapshot['SnapshotId'], new_tags))
    #                     ec2.create_tags(Resources=[snapshot['SnapshotId']], Tags=ansible_dict_to_boto3_tag_list(new_tags))
    #         except:
    #             logger.info('{0}: Invalid value in Ebs')

    # for snapshot in snapshots.values():
    #     if 'Used' not in snapshot:
    #         cur_tags = boto3_tag_list_to_ansible_dict(snapshot.get('Tags', []))
    #         name = cur_tags.get('Name', snapshot['SnapshotId'])
    #         if not name.startswith('UNUSED'):
    #             logger.warning('{0} Unused!'.format(snapshot['SnapshotId']))
    #             cur_tags['Name'] = 'UNUSED ' + name
    #             ec2.create_tags(Resources=[snapshot['SnapshotId']], Tags=ansible_dict_to_boto3_tag_list(cur_tags))



def handler(event, context):
    copy_AMI()

if __name__ == '__main__':
    copy_AMI()
