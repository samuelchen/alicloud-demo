'''
Created on Mar 29, 2018

@author: zhuzhou
'''
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.acs_exception.exceptions import ServerException
import time
import json
import logging

log = logging.getLogger(__name__)

class VpcManager(object):
    
    def __init__(self, access_key_id, access_key_secret, region_id):
        self.region_id = region_id
        self.client = AcsClient(access_key_id, access_key_secret, region_id)
        pass
    

    def create_or_select_vpc(self, vpc_name, vpc_cidr, vswitch_obj):
        vpc_existed = False
        vpc_list = self.list_vpcs()
        vpc_id = ""
        vpc_already_existed = False
        for vpc in vpc_list:
            if vpc.name == vpc_name:
                vswitch_obj.vpc_id = vpc.id
                vpc_existed = True
                vpc_id = vpc.id
                vpc_already_existed = True
                break
        
        if not vpc_existed:
            log.info("This VPC (%s) not existed, will create "%(vpc_name))
            vpc_obj = self.create_vpc(vpc_name, vpc_cidr)
            vswitch_obj.vpc_id = vpc_obj.id
            vpc_id = vpc_obj.id
            log.info("VPC created ok!")
        return vpc_already_existed, vpc_id
    
    def select_or_create_switch(self, vpc_id, vswitch_obj):
        switch_list = self.list_vswitches(vpc_id)
        selected_switch = None
        switch_already_existed = False
        for sw in switch_list:
            if sw.vswitch_name == vswitch_obj.vswitch_name:
                selected_switch = sw
                switch_already_existed = True
                break
        if selected_switch is None:
            log.info("This switch (%s) not existed, will create "%(vswitch_obj.vswitch_name))
            vswitch_obj.create_vswitch(self)
            selected_switch = vswitch_obj
            log.info("Vswitch created ok!")
            
        return switch_already_existed, selected_switch
                

    def create_vpc_all_in_one(self, vpc_name, vpc_cidr, vswitch_obj):
        vpc_already_existed, vpc_id = self.create_or_select_vpc(vpc_name, vpc_cidr, vswitch_obj)
        if not vpc_already_existed:
            log.info("Waiting for new created VPC to be available")
            time.sleep(20)
        vswitch_already_existed, vswitch_obj = self.select_or_create_switch(vpc_id, vswitch_obj)
        if not vswitch_already_existed:
            log.info("Waiting for new created Vswitch to be available")
            time.sleep(20)
        #Create some instances
        nat_already_exist, nat = self.select_or_create_clean_nat(vpc_id)
        
        if not nat_already_exist:
            log.info("Waiting for new created NAT to be available")
            time.sleep(10)
        #allocate eip
        
        eip = self.associate_eip_with_nat(nat.nat_gateway_id)
        log.info("Waiting for new NAT rule to be ready")
        time.sleep(10)
        
        return vpc_id, vswitch_obj.vswitch_id, nat.nat_gateway_id, eip.eip_address
        
    def create_vpc(self, vpc_name, vpc_cidr, vpc_description=""):
        vpc = Vpc(name=vpc_name, cidr=vpc_cidr)
        vpc = vpc.create_vpc(self)
        return vpc
    
    def delete_vpc(self, vpc_id):
        vpc = Vpc()
        vpc.set_id(vpc_id)
        return vpc.delete_vpc(self)
    
    def list_vpcs(self):
        req = DescribeVpcsRequest.DescribeVpcsRequest()
        response_dict = self._do_action(req)
        vpc_list = response_dict["Vpcs"]["Vpc"]
        vpc_obj_list = []
        for vpc in vpc_list:
            vpc_obj = Vpc()
            vpc_obj._load(vpc)
            vpc_obj_list.append(vpc_obj)
        return vpc_obj_list
    
    ##########Switch related functions########################
    def delete_all_switch(self, vpc_id):
        switch_list = self.list_vswitches(vpc_id)
        for sw in switch_list:
            self.delete_vswitch(sw.vswitch_id)
            
    def delete_all_nat(self, vpc_id):
        nat_list = self.list_nats(vpc_id)
        for nat in nat_list:
            self.delete_nat(vpc_id, nat.nat_gateway_id)
        
    def list_vswitches(self, vpc_id):
        req = DescribeVSwitchesRequest.DescribeVSwitchesRequest()
        req.set_VpcId(vpc_id)
#         req.set_ZoneId(zone_id)
        response_dict = self._do_action(req)
        vswitch_res = response_dict["VSwitches"]["VSwitch"]
        vs_list = []
        for vs in vswitch_res:
            vs_obj = VSwitch()
            vs_obj.load_after_describe(vs)
            vs_list.append(vs_obj)
        return vs_list

    def create_vswitch(self, zone_id, cidr_block, vpc_id, vswitch_name):
        vs = VSwitch(vpc_id=vpc_id, zone_id=zone_id, vswitch_name=vswitch_name, cidr_block=cidr_block)
        vs.create_vswitch()
        return vs

    def delete_vswitch(self, vswitch_id):
        return VSwitch().delete(vswitch_id, self)

########NAT related functions###############
    def create_nat(self, vpc_id):
        nat = NAT(vpc_id)
        req = nat.gen_create_nat_req()
        req.set_VpcId(vpc_id)
        resp = self._do_action(req)
        nat._load_after_create_nat(resp)
        return nat
    
    def select_or_create_clean_nat(self, vpc_id, capacity_limit=2):
        """
        If there are free nat, then it will return the first free nat,
        If not, it will check total if nat number is under limit,
           if yes, it will create one nat
           if no, it will raise Exception
        """
        nat_list = self.list_nats(vpc_id)
        selected_nat = None
        nat_already_existed = False
        eip_list = self.list_eips()
        for nat in nat_list:
            used_nat_gateway_ids = []
            for eip in eip_list:
                used_nat_gateway_ids.append(eip.instance_id)
                
            if nat.nat_gateway_id not in used_nat_gateway_ids:
                selected_nat = nat
                nat_already_existed = True
                break
            
        if selected_nat is None:
            if len(nat_list) >= capacity_limit:
                raise Exception("There are two NATs which allocated EIP already, please release and reuse them!")
            selected_nat = self.create_nat(vpc_id)
        return nat_already_existed, selected_nat

    def list_nats(self, vpc_id):
        nat = NAT(vpc_id)
        req = nat._gen_list_nat_req()
        resp = self._do_action(req)
        nat_list = []
        for nat_dict in resp["NatGateways"]["NatGateway"]:
            obj = NAT(vpc_id)
            obj._load_after_list_nat(nat_dict)
            nat_list.append(obj)
        return nat_list
    
    def add_nat_rules(self, vpc_id, nat_gateway_id, nat_rule_obj_list):
        nat_list = self.list_nats(vpc_id)
        selected_nat = None
        for nat in nat_list:
            if nat.nat_gateway_id == nat_gateway_id:
                selected_nat = nat
        if selected_nat is None:
            raise Exception("No such nat with id: "+nat_gateway_id)
        for nat_rule_obj in nat_rule_obj_list:
            selected_nat.add_nat_rule(nat_rule_obj, self)
    
    def delete_nat(self, vpc_id, nat_gateway_id):
        nat = NAT(vpc_id)
        req = nat.gen_delete_nat_req(vpc_id, nat_gateway_id)
        self._do_action(req)
    
    def associate_eip_with_nat(self, nat_gateway_id, eip_address = None):
        eip_already_existed, eip = self.select_or_allocate_eip()
        if not eip_already_existed:
            time.sleep(20)
        req = eip.gen_associate_eip_req(eip.allocation_id, nat_gateway_id)
        self._do_action(req)
        return eip
    
    def select_or_allocate_eip(self, capacity_limit=2):
        """
        If total eip number greater equals or than capacity limit, it will return the unassociate eip,
        if no such eip, it will raise Exception
        If total eip number is under capacity limit, it still will return the unssociate eip first,
        but if there's no free eip, it will create one
        """
        eip_list = self.list_eips()
        selected_eip = None
        eip_already_existed = False
        if len(eip_list) >= capacity_limit:
            for eip in eip_list:
                if eip.instance_id is None or eip.instance_id == "":
                    selected_eip = eip
                    eip_already_existed = True
                    break
            if not eip_already_existed:
                raise Exception("There are two eips already, please release them first")
        if not eip_already_existed:
            eip = EIP()
            req = eip.gen_allocate_eip_req()
            res = self._do_action(req)
            eip.load_after_allocate(res)
            selected_eip = eip
        return eip_already_existed, selected_eip
        
    def list_eips(self):
        eip = EIP()
        req = eip.gen_describe_eip_req()
        res = self._do_action(req)
        res_dict = res["EipAddresses"]["EipAddress"]
        eip_list = []
        for res in res_dict:
            obj = EIP()
            obj.load_after_describe(res)
            eip_list.append(obj)
        return eip_list
                    
    def unassociate_eip_from_nat(self, allocation_id, instance_id):
        eip = EIP()
        req = eip.gen_unassociate_eip_req(allocation_id, instance_id)
        self._do_action(req)
    
    def release_eip(self, allocation_id):
        eip = EIP()
        req = eip.gen_release_eip_req(allocation_id)
        res = self._do_action(req)

    def _do_action(self, req):
        try:
            response = self.client.do_action_with_exception(req)
            response_dict = json.loads(response)
            return response_dict
        except ClientException as ce:
            print(ce)
        except ServerException as se:
            print(se)
        except Exception as e:
            print(e)
    

from aliyunsdkvpc.request.v20160428 import CreateVpcRequest
from aliyunsdkvpc.request.v20160428 import DeleteVpcRequest
from aliyunsdkvpc.request.v20160428 import DescribeVpcsRequest
class Vpc(object):
    
    def __init__(self, name="", cidr=""):
        self.id = None
        self.name = name
        self.cidr = cidr
        self.zones = []
        self.zone_switch = {}
        self.status = ""

    def create_vpc(self, manager):
        req = self.__gen_create_vpc_req()
        response_dict = manager._do_action(req)
        self.__load_after_create(response_dict)
        return self
    
    def delete_vpc(self, manager):
        req = DeleteVpcRequest.DeleteVpcRequest()
        req.set_VpcId(self.id)
        return manager._do_action(req)
            
    def __gen_create_vpc_req(self):
        req = CreateVpcRequest.CreateVpcRequest()
        req.set_VpcName(self.name)
        req.set_CidrBlock(self.cidr)
        req.set_ClientToken(str(time.time()))
        return req
    
    def _load(self, response_dict):
        self._origin_response_ = response_dict
        self.name = response_dict["VpcName"]
        self.cidr = response_dict["CidrBlock"]
        self.id = response_dict["VpcId"]
        self.desc = response_dict["Description"]
        self.zones = []
        self.zone_switch = {}
        self.route_id = response_dict["VRouterId"]
        self.route_table_id = response_dict["RouterTableIds"]
        
    def __load_after_create(self, response_dict):
        self._origin_response_ = response_dict
        self.id = response_dict["VpcId"]
        self.route_id = response_dict["VRouterId"]
        self.route_table_id = response_dict["RouteTableId"]
    
    def _check_if_can_delete(self, zone_id, vswitch_id):
        return False
    
    def set_id(self, vpc_id):
        self.id = vpc_id
    
    def set_route_id(self, route_id):
        self.route_id = route_id
        
    def set_route_table_id(self, route_table_id):
        self.route_table_id = route_table_id
    
    def get_vswitch_by_zone(self, zone_id):
        switch_list = self.zone_switch[zone_id]
        if switch_list is None:
            return []
        else:
            return switch_list
    
    def list_zones(self):
        return self.zones
    
    def configure_route(self):
        pass

from aliyunsdkvpc.request.v20160428 import CreateVSwitchRequest
from aliyunsdkvpc.request.v20160428 import DescribeVSwitchesRequest
from aliyunsdkvpc.request.v20160428 import DeleteVSwitchRequest
class VSwitch(object):
    
    def __init__(self, vpc_id="", zone_id="", vswitch_id="", vswitch_name="", cidr_block=""):
        self.vpc_id = vpc_id
        self.zone_id = zone_id
        self.vswitch_id = vswitch_id
        self.vswitch_name = vswitch_name
        self.cidr_block = cidr_block
        
    def delete(self, vswitch_id, manager):
        req = self.gen_delete_switch_req(vswitch_id)
        manager._do_action(req)
        
    def load_after_describe(self, res):
        self._origin_response_ = res
        self.vpc_id = res["VpcId"]
        self.zone_id = res["ZoneId"]
        self.vswitch_id = res["VSwitchId"]
        self.vswitch_name = res["VSwitchName"]
        self.cidr_block = res["CidrBlock"]
    
    def gen_create_req(self):
        req = CreateVSwitchRequest.CreateVSwitchRequest()
        req.set_CidrBlock(self.cidr_block)
        req.set_ZoneId(self.zone_id)
        req.set_VpcId(self.vpc_id)
        req.set_VSwitchName(self.vswitch_name)
        return req
    
    def _load(self, response_dict):
        self._origin_response_ = response_dict
        self.set_id(response_dict["VpcId"])
        self.set_route_id(response_dict["VRouterId"])
        self.set_route_table_id(response_dict["RouteTableId"])
        
    def gen_delete_switch_req(self, vswitch_id):
        req = DeleteVSwitchRequest.DeleteVSwitchRequest()
        req.set_VSwitchId(vswitch_id)
        return req
    
    def create_vswitch(self, manager):
        req = self.gen_create_req()
        response_dict = manager._do_action(req)
        self.vswitch_id = response_dict["VSwitchId"]
        return self

from aliyunsdkvpc.request.v20160428 import CreateNatGatewayRequest
from aliyunsdkvpc.request.v20160428 import DeleteNatGatewayRequest
from aliyunsdkvpc.request.v20160428 import DescribeNatGatewaysRequest
from aliyunsdkvpc.request.v20160428 import CreateForwardEntryRequest
from aliyunsdkvpc.request.v20160428 import DeleteForwardEntryRequest
class NAT(object):
    
    def __init__(self, vpc_id):
        self.vpc_id = vpc_id
        self.nat_gateway_id = ""
        self.forward_table_ids = []
        self.nat_rules = []
        self.bandwith_package = []
        self.status = ""
        
    def _load_after_create_nat(self, response):
        self._origin_response_ = response
        self.nat_gateway_id = response["NatGatewayId"]
        self.forward_table_ids = response["ForwardTableIds"]["ForwardTableId"]
        
    def _load_after_create_nat_rule(self, response):
        self._origin_response_ = response
        
    def _load_after_list_nat_rule(self, response):
        self._origin_response_ = response
        #Because this is a list operation, the existing rule should be empty
        #to avoid duplicate rule
        self.nat_rules = []
        entry_list = response["ForwardTableEntries"]["ForwardTableEntry"]
        for entry in entry_list:
            self.nat_rules.append(entry)
    
    def _gen_list_nat_req(self):
        req = DescribeNatGatewaysRequest.DescribeNatGatewaysRequest()
        req.set_VpcId(self.vpc_id)
        return req
    
    def _load_after_list_nat(self, response):
        self._origin_response_ = response
        self.nat_gateway_id = response["NatGatewayId"]
        self.forward_table_ids = response["ForwardTableIds"]["ForwardTableId"]
        self.bandwith_package = response["BandwidthPackageIds"]
        self.status = response["Status"]
        
            
    def gen_create_nat_req(self):
        req = CreateNatGatewayRequest.CreateNatGatewayRequest()
        req.set_VpcId(self.vpc_id)
        return req
    
    def gen_delete_nat_req(self, vpc_id, nat_gateway_id):
        req = DeleteNatGatewayRequest.DeleteNatGatewayRequest()
        req.set_NatGatewayId(nat_gateway_id)
        return req
    
    def gen_create_forward_route_req(self, nat_rule_obj):
        req = CreateForwardEntryRequest.CreateForwardEntryRequest()
        if len(self.forward_table_ids) == 0:
            raise Exception("No forward table id")
        req.set_ForwardTableId(self.forward_table_ids[0])
        req.set_ExternalIp(nat_rule_obj.exter_ip)
        req.set_ExternalPort(nat_rule_obj.exter_port)
        req.set_IpProtocol(nat_rule_obj.protocol)
        req.set_InternalIp(nat_rule_obj.inter_ip)
        req.set_InternalPort(nat_rule_obj.inter_port)
        return req

    def add_nat_rule(self, nat_rule_obj, manager):
        req = self.gen_create_forward_route_req(nat_rule_obj)
        res = manager._do_action(req)
        self._load_after_create_nat_rule(res)

class NATRule(object):
    
    def __init__(self, exter_ip, exter_port, protocol, inter_ip, inter_port):
        self.exter_ip = exter_ip
        self.exter_port = exter_port
        self.protocol = protocol
        self.inter_ip = inter_ip
        self.inter_port = inter_port
    pass


from aliyunsdkvpc.request.v20160428 import AllocateEipAddressRequest
from aliyunsdkvpc.request.v20160428 import AssociateEipAddressRequest
from aliyunsdkvpc.request.v20160428 import UnassociateEipAddressRequest
from aliyunsdkvpc.request.v20160428 import ReleaseEipAddressRequest
from aliyunsdkvpc.request.v20160428 import DescribeEipAddressesRequest
class EIP(object):
    
    def __init__(self):
        self.allocation_id = None
        self.instance_id = None
        self.eip_address = None
    
    def gen_allocate_eip_req(self):
        req = AllocateEipAddressRequest.AllocateEipAddressRequest()
        return req
    
    def gen_associate_eip_req(self, allocation_id, instance_id):
        req = AssociateEipAddressRequest.AssociateEipAddressRequest()
        req.set_InstanceType("NAT")
        req.set_AllocationId(allocation_id)
        req.set_InstanceId(instance_id)
        return req
    
    def gen_unassociate_eip_req(self, allocation_id, instance_id):
        req = UnassociateEipAddressRequest.UnassociateEipAddressRequest()
        req.set_AllocationId(allocation_id)
        req.set_InstanceId(instance_id)
        return req
    
    def gen_describe_eip_req(self):
        req = DescribeEipAddressesRequest.DescribeEipAddressesRequest()
        return req
    
    def gen_release_eip_req(self, allocation_id):
        req = ReleaseEipAddressRequest.ReleaseEipAddressRequest()
        req.set_AllocationId(allocation_id)
        return req
    
    def load_after_allocate(self, response_dict):
        self._origin_response_ = response_dict
        self.allocation_id = response_dict["AllocationId"]
        self.eip_address = response_dict["EipAddress"]
    
    def load_after_describe(self, response_dict):
        self._origin_response_ = response_dict
        self.allocation_id = response_dict["AllocationId"]
        self.instance_id = response_dict["InstanceId"]
        self.eip_address = response_dict["IpAddress"]
        
def test_create_vpc_all_in_one(arg1, arg2, arg3):
        vpc_manager = VpcManager(arg1, arg2, arg3)
        region_id = arg3
        
        vpc_name = "test4"
        vpc_cidr = "192.168.0.0/16"
        public_ip = "202.202.202.202"
        vswitch_obj = VSwitch()
        vswitch_obj.vswitch_name = "Demo2"
        vswitch_obj.cidr_block = "192.168.2.0/24"
        vswitch_obj.zone_id = region_id+"-a"
           
         
        vpc_id, vswitch_id, nat_gateway_id, eip = vpc_manager.create_vpc_all_in_one(vpc_name, vpc_cidr, vswitch_obj)
        #Do create vm
        #Get vm's ip address
        vm_ip = ""
        rule1 = NATRule(eip, "8080", "TCP", vm_ip, "8080")
        nat_rule_obj_list = [rule1]
        vpc_manager.add_nat_rules(vpc_id, nat_gateway_id, nat_rule_obj_list)

def test_delete_all_vpc(arg1, arg2, arg3):
    vpc_manager = VpcManager(arg1, arg2, arg3)
    vpcs = vpc_manager.list_vpcs()
    for vpc in vpcs:
        print(vpc._origin_response_)
        switch_list = vpc_manager.list_vswitches(vpc.id)
        for sw in switch_list:
            print (sw.vswitch_id)
             
        vpc_manager.delete_all_switch(vpc.id)
        vpc_manager.delete_all_nat(vpc.id)
        vpc_manager.delete_vpc(vpc.id)
        print("VPC has been deleted with id: " + vpc.id)

def test_add_nat_rules(arg1, arg2, arg3):
    vpc_manager = VpcManager(arg1, arg2, arg3)
    vpcs = vpc_manager.list_vpcs()
    for vpc in vpcs:
        nats = vpc_manager.list_nats(vpc.id)
        for nat in nats:
            rule = NATRule("202.202.202.202", "8080", "TCP", "192.168.1.10", "8080")
            nat.add_nat_rule(rule)

def test_eip_allocation(arg1, arg2, arg3):
    vpc_manager = VpcManager(arg1, arg2, arg3)
    eip = vpc_manager.allocate_eip()
    print(eip.allocation_id + " " +eip.eip_address)
    eip_list = vpc_manager.list_eips()
    for obj in eip_list:
        print("This ip: " + obj.eip_address + "will be released soon.")
        
def test_list_all_nat(arg1, arg2, arg3):
    vpc_manager = VpcManager(arg1, arg2, arg3)
    nat_list = vpc_manager.list_nats("vpc-bp1x0rrinawjcd3ejlx0a")
    for nat in nat_list:
        print(nat._origin_response_)
#         vpc_manager.release_eip(obj.allocation_id)
#         print("EIP released!")
    
if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 4:
#         test_eip_allocation(sys.argv[1], sys.argv[2], sys.argv[3])
#         test_create_vpc_all_in_one(sys.argv[1], sys.argv[2], sys.argv[3])
        test_delete_all_vpc(sys.argv[1], sys.argv[2], sys.argv[3])
#         test_list_all_nat(sys.argv[1], sys.argv[2], sys.argv[3])
#         test_add_nat_rules(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        print ("Should pass 3 parameters: access_key_id, access_key_secret, region_id")
        