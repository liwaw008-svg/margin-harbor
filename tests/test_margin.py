from conftest import CONTRACT
U=['https://terms.example/p1','https://market-a.example/p1','https://market-b.example/p1']
def mocks(v):
 v.strict_mocks=True;v.check_pickling=True;v.mock_web(r'terms\.example',{'status':200,'body':'Collateral 150, debt 100, warning below 125.'});v.mock_web(r'market-a\.example',{'status':200,'body':'Observed collateral value 150.'});v.mock_web(r'market-b\.example',{'status':200,'body':'Independent value 148.'});v.mock_llm(r'.*Calculate bounded.*','{"health":149,"state":"WATCHING","signal_codes":["ABOVE_WARNING"]}');v.mock_llm(r'.*Verify exact health.*','{"valid":true}')
def test_epochs(direct_vm,direct_deploy):
 c=direct_deploy(CONTRACT);mocks(direct_vm);c.watch('P1','warning below 125',U);c.refresh('P1',1);s=c.get_position('P1');assert s['health']==149 and s['epoch']==1;c.acknowledge_recovery('P1');assert c.get_position('P1')['state']=='RECOVERED'
def test_stale_sources(direct_vm,direct_deploy):
 c=direct_deploy(CONTRACT);c.watch('A','terms',U)
 with direct_vm.expect_revert('duplicate'):c.watch(' a ','terms',U)
 with direct_vm.expect_revert('independent'):c.watch('B','terms',[U[0],U[0],U[2]])
 mocks(direct_vm);c.refresh('A',2)
 with direct_vm.expect_revert('fresh active'):c.refresh('A',2)
def test_forged_health(direct_vm,direct_deploy):
 c=direct_deploy(CONTRACT);mocks(direct_vm);c.watch('X','terms',U);x=c._check(c.positions['X'],1);assert direct_vm.run_validator(leader_result=x);x=dict(x);x['health']=201;assert not direct_vm.run_validator(leader_result=x)
