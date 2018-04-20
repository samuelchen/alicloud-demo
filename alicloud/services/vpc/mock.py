'''
Created on Mar 31, 2018

@author: zhuzhou
'''
from aliyunsdkvpc.request.v20160428 import AllocateEipAddressRequest
from aliyunsdkvpc.request.v20160428 import AssociateEipAddressRequest
from aliyunsdkvpc.request.v20160428 import UnassociateEipAddressRequest
from aliyunsdkvpc.request.v20160428 import ReleaseEipAddressRequest
from aliyunsdkvpc.request.v20160428 import DescribeEipAddressesRequest
from aliyunsdkvpc.request.v20160428 import CreateNatGatewayRequest
from aliyunsdkvpc.request.v20160428 import DeleteNatGatewayRequest
from aliyunsdkvpc.request.v20160428 import DescribeNatGatewaysRequest
from aliyunsdkvpc.request.v20160428 import CreateForwardEntryRequest
from aliyunsdkvpc.request.v20160428 import DeleteForwardEntryRequest
from aliyunsdkvpc.request.v20160428 import CreateVSwitchRequest
from aliyunsdkvpc.request.v20160428 import DescribeVSwitchesRequest
from aliyunsdkvpc.request.v20160428 import DeleteVSwitchRequest
from aliyunsdkvpc.request.v20160428 import CreateVpcRequest
from aliyunsdkvpc.request.v20160428 import DeleteVpcRequest
from aliyunsdkvpc.request.v20160428 import DescribeVpcsRequest

from alicloud.services.vpc import vpc_service
class VpcManagerMock(vpc_service.VpcManager):
    
    def _do_action(self, req):
        create_vswitch_mock = {"RequestId": "861E6630-AEC0-4B2D-B214-6CB5E44B7F04",
                              "VSwitchId": "vsw-25naue4gz"
        }
        create_vpc_mock = {"RequestId": "461D0C42-D5D1-4009-9B6A-B3D5888A19A9",
                           "RouteTableId": "vtb-25wm68mnh",
                           "VRouterId": "vrt-25bezkd03",
                           "VpcId": "vpc-257gq642n"
        }
        delete_vpc_mock = {"RequestId":"606998F0-B94D-48FE-8316-ACA81BB230DA"}
        delete_vswitch_mock = {"RequestId": "AF083E3D-7E29-4B77-A937-1F129802D5F3"}
        describe_vswitch_mock = {
          "PageNumber": 1,
          "PageSize": 10,
          "RequestId": "9A572171-4E27-40D1-BD36-D26C9E71E29E",
          "TotalCount": 1,
          "VSwitches": {
            "VSwitch": [
              {
                "AvailableIpAddressCount": 246,
                "CidrBlock": "172.16.1.0/24",
                "CreationTime": "2014-10-29T15:21:02Z",
                "Description": "",
                "Status": "Available",
                "VSwitchId": "vsw-25b7pv15t",
                "VSwitchName": "",
                "VpcId": "vpc-257gq642n",
                "ZoneId": "cn-beijing-a"
              }
            ]
          }
        }
        
        describe_vpc_mock = {
    'PageNumber': 1,
    'Vpcs': {
        'Vpc': [{
            'CreationTime': '2018-03-30T02:56:46Z',
            'CidrBlock': '192.168.0.0/16',
            'VpcName': 'test_vpc2',
            'Status': 'Available',
            'Description': '',
            'VSwitchIds': {
                'VSwitchId': []
            },
            'IsDefault': False,
            'NatGatewayIds': {
                'NatGatewayIds': []
            },
            'UserCidrs': {
                'UserCidr': []
            },
            'ResourceGroupId': 'rg-acfmzmiqxjyibry',
            'RegionId': 'cn-hangzhou',
            'RouterTableIds': {
                'RouterTableIds': ['vtb-bp1morlfefqefmkpp5hke']
            },
            'VRouterId': 'vrt-bp1j6u9sofopvuaq9gsh9',
            'VpcId': 'vpc-bp1kgesrqlck6dzxb6vqk'
        }, {
            'CreationTime': '2018-03-30T02:56:18Z',
            'CidrBlock': '192.168.0.0/16',
            'VpcName': 'test_vpc1',
            'Status': 'Available',
            'Description': '',
            'VSwitchIds': {
                'VSwitchId': []
            },
            'IsDefault': False,
            'NatGatewayIds': {
                'NatGatewayIds': []
            },
            'UserCidrs': {
                'UserCidr': []
            },
            'ResourceGroupId': 'rg-acfmzmiqxjyibry',
            'RegionId': 'cn-hangzhou',
            'RouterTableIds': {
                'RouterTableIds': ['vtb-bp1vzuhd2yx2tbghwf67p']
            },
            'VRouterId': 'vrt-bp1ujwa4sl9hykohsamno',
            'VpcId': 'vpc-bp1x6u1nu3262jpzgvzg3'
        }, {
            'CreationTime': '2018-03-29T07:46:11Z',
            'CidrBlock': '192.168.0.0/16',
            'VpcName': 'test_vpc1',
            'Status': 'Available',
            'Description': '',
            'VSwitchIds': {
                'VSwitchId': []
            },
            'IsDefault': False,
            'NatGatewayIds': {
                'NatGatewayIds': []
            },
            'UserCidrs': {
                'UserCidr': []
            },
            'ResourceGroupId': 'rg-acfmzmiqxjyibry',
            'RegionId': 'cn-hangzhou',
            'RouterTableIds': {
                'RouterTableIds': ['vtb-bp1j7r2z51ee8lo6xbicp']
            },
            'VRouterId': 'vrt-bp1g0wyd11j4529nq3d0o',
            'VpcId': 'vpc-bp1v6e2a20wp3vfoxf2cn'
        }, {
            'CreationTime': '2018-03-29T07:45:33Z',
            'CidrBlock': '192.168.0.0/16',
            'VpcName': 'test_vpc1',
            'Status': 'Available',
            'Description': '',
            'VSwitchIds': {
                'VSwitchId': []
            },
            'IsDefault': False,
            'NatGatewayIds': {
                'NatGatewayIds': []
            },
            'UserCidrs': {
                'UserCidr': []
            },
            'ResourceGroupId': 'rg-acfmzmiqxjyibry',
            'RegionId': 'cn-hangzhou',
            'RouterTableIds': {
                'RouterTableIds': ['vtb-bp1kj4rx8mtf6y3k4d7x1']
            },
            'VRouterId': 'vrt-bp1jy64smreus0k1rc0no',
            'VpcId': 'vpc-bp15id6rlfmi46q633m1f'
        }, {
            'VpcName': '',
            'Description': 'System created default VPC.',
            'IsDefault': True,
            'ResourceGroupId': 'rg-acfmzmiqxjyibry',
            'UserCidrs': {
                'UserCidr': []
            },
            'NatGatewayIds': {
                'NatGatewayIds': []
            },
            'RouterTableIds': {
                'RouterTableIds': ['vtb-bp1gmae7z11maof1v3lpb']
            },
            'VpcId': 'vpc-bp11stai0nk45aa0h5db1',
            'VRouterId': 'vrt-bp18fr4dxg1q29nfy8dcu',
            'CreationTime': '2018-03-25T14:33:33Z',
            'Status': 'Available',
            'CidrBlock': '172.16.0.0/16',
            'VSwitchIds': {
                'VSwitchId': ['vsw-bp12mh8owpak26vr41k36', 'vsw-bp15f59kh9l3sv9ysj5v8']
            },
            'RegionId': 'cn-hangzhou'
        }]
    },
    'TotalCount': 5,
    'PageSize': 10,
    'RequestId': 'E46A354F-7DD3-4991-A6BF-F336E6258650'
}
        response_mapping = {
                            str(CreateVSwitchRequest.CreateVSwitchRequest) : create_vswitch_mock,
                            str(CreateVpcRequest.CreateVpcRequest) : create_vpc_mock,
                            str(DeleteVpcRequest.DeleteVpcRequest) : delete_vpc_mock,
                            str(DeleteVSwitchRequest.DeleteVSwitchRequest) : delete_vswitch_mock,
                            str(DescribeVpcsRequest.DescribeVpcsRequest) : describe_vpc_mock,
                            str(DescribeVSwitchesRequest.DescribeVSwitchesRequest) : describe_vswitch_mock,
                            "":""
                            }
        key = str(type(req))
        return response_mapping[key]
