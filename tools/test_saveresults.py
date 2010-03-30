# -*- coding: utf-8 -*-
import saveresults
import unittest

class testSaveresults(unittest.TestCase):
    '''Tests Saveresults script for saving data to speed.pypy.org'''
    fixture = [
        ['ai', 'ComparisonResult', {'avg_base': 0.42950453758219992, 'timeline_link': None, 'avg_changed': 0.43322672843939997, 'min_base': 0.42631793022199999, 'delta_min': '1.0065x faster', 'delta_avg': '1.0087x slower', 'std_changed': 0.0094009621054567376, 'min_changed': 0.423564910889, 'delta_std': '2.7513x larger', 'std_base': 0.0034169249420902843, 't_msg': 'Not significant\n'}],
        ['chaos', 'ComparisonResult', {'avg_base': 0.41804099082939999, 'timeline_link': None, 'avg_changed': 0.11744904518135998, 'min_base': 0.41700506210299998, 'delta_min': '9.0148x faster', 'delta_avg': '3.5593x faster', 'std_changed': 0.14350186143481433, 'min_changed': 0.046257972717299999, 'delta_std': '108.8162x larger', 'std_base': 0.0013187546718754512, 't_msg': 'Significant (t=4.683672, a=0.95)\n'}],
        ['django', 'ComparisonResult', {'avg_base': 0.83651852607739996, 'timeline_link': None, 'avg_changed': 0.48571481704719999, 'min_base': 0.82990884780899998, 'delta_min': '1.7315x faster', 'delta_avg': '1.7222x faster', 'std_changed': 0.006386606999421761, 'min_changed': 0.47929787635799997, 'delta_std': '1.7229x smaller', 'std_base': 0.011003382690633789, 't_msg': 'Significant (t=61.655971, a=0.95)\n'}],
        ['fannkuch', 'ComparisonResult', {'avg_base': 1.8561528205879998, 'timeline_link': None, 'avg_changed': 0.38401727676399999, 'min_base': 1.84801197052, 'delta_min': '5.0064x faster', 'delta_avg': '4.8335x faster', 'std_changed': 0.029594360755246251, 'min_changed': 0.36913013458299998, 'delta_std': '3.2353x larger', 'std_base': 0.0091472519207758066, 't_msg': 'Significant (t=106.269998, a=0.95)\n'}],
        ['float', 'ComparisonResult', {'avg_base': 0.50523018836940004, 'timeline_link': None, 'avg_changed': 0.15490598678593998, 'min_base': 0.49911379814099999, 'delta_min': '6.2651x faster', 'delta_avg': '3.2615x faster', 'std_changed': 0.057739598339608837, 'min_changed': 0.079665899276699995, 'delta_std': '7.7119x larger', 'std_base': 0.007487037523761327, 't_msg': 'Significant (t=13.454285, a=0.95)\n'}], ['gcbench', 'SimpleComparisonResult', {'base_time': 27.236408948899999, 'changed_time': 5.3500790595999996, 'time_delta': '5.0908x faster'}],
        ['html5lib', 'SimpleComparisonResult', {'base_time': 11.666918992999999, 'changed_time': 12.6703209877, 'time_delta': '1.0860x slower'}],
        ['richards', 'ComparisonResult', {'avg_base': 0.29083266258220003, 'timeline_link': None, 'avg_changed': 0.029299402236939998, 'min_base': 0.29025602340700002, 'delta_min': '10.7327x faster', 'delta_avg': '9.9262x faster', 'std_changed': 0.0033452973342946888, 'min_changed': 0.027044057846099999, 'delta_std': '5.6668x larger', 'std_base': 0.00059033067516221327, 't_msg': 'Significant (t=172.154488, a=0.95)\n'}],
        ['rietveld', 'ComparisonResult', {'avg_base': 0.46909418106079998, 'timeline_link': None, 'avg_changed': 1.312631273269, 'min_base': 0.46490097045899997, 'delta_min': '2.1137x slower', 'delta_avg': '2.7982x slower', 'std_changed': 0.44401595627955542, 'min_changed': 0.98267102241500004, 'delta_std': '76.0238x larger', 'std_base': 0.0058404831974135556, 't_msg': 'Significant (t=-4.247692, a=0.95)\n'}],
        ['slowspitfire', 'ComparisonResult', {'avg_base': 0.66740002632140005, 'timeline_link': None, 'avg_changed': 1.6204295635219998, 'min_base': 0.65965509414699997, 'delta_min': '1.9126x slower', 'delta_avg': '2.4280x slower', 'std_changed': 0.27415559151786589, 'min_changed': 1.26167798042, 'delta_std': '20.1860x larger', 'std_base': 0.013581457669479846, 't_msg': 'Significant (t=-7.763579, a=0.95)\n'}],
        ['spambayes', 'ComparisonResult', {'avg_base': 0.279049730301, 'timeline_link': None, 'avg_changed': 1.0178018569945999, 'min_base': 0.27623891830399999, 'delta_min': '3.3032x slower', 'delta_avg': '3.6474x slower', 'std_changed': 0.064953583956645466, 'min_changed': 0.91246294975300002, 'delta_std': '28.9417x larger', 'std_base': 0.0022442880892229711, 't_msg': 'Significant (t=-25.416839, a=0.95)\n'}],
        ['spectral-norm', 'ComparisonResult', {'avg_base': 0.48315834999099999, 'timeline_link': None, 'avg_changed': 0.066225481033300004, 'min_base': 0.476922035217, 'delta_min': '8.0344x faster', 'delta_avg': '7.2957x faster', 'std_changed': 0.013425108838933627, 'min_changed': 0.059360027313200003, 'delta_std': '1.9393x larger', 'std_base': 0.0069225510731835901, 't_msg': 'Significant (t=61.721418, a=0.95)\n'}],
        ['spitfire', 'ComparisonResult', {'avg_base': 7.1179999999999994, 'timeline_link': None, 'avg_changed': 7.2780000000000005, 'min_base': 7.04, 'delta_min': '1.0072x faster', 'delta_avg': '1.0225x slower', 'std_changed': 0.30507376157250898, 'min_changed': 6.9900000000000002, 'delta_std': '3.4948x larger', 'std_base': 0.08729261137118062, 't_msg': 'Not significant\n'}],
        ['twisted_iteration', 'SimpleComparisonResult', {'base_time': 0.148289627437, 'changed_time': 0.035354803126799998, 'time_delta': '4.1943x faster'}],
        ['twisted_web', 'SimpleComparisonResult', {'base_time': 0.11312217194599999, 'changed_time': 0.625, 'time_delta': '5.5250x slower'}]
    ]
    
    def testGoodInput(self):
        '''Given correct result data, check that every result being saved has the right parameters'''
        for resultparams in saveresults.save("pypy", 71212, self.fixture, "", "experimental", "pypy-c-jit", "gc=hybrid", True):
            self.assertEqual(resultparams['revision_project'], "pypy")
            self.assertEqual(resultparams['revision_number'], 71212)
            self.assertEqual(resultparams['revision_branch'], "experimental")
            self.assertEqual(resultparams['interpreter_name'], "pypy-c-jit")
            self.assertEqual(resultparams['interpreter_coptions'], "gc=hybrid")
            # get dict with correct data for this benchmark
            fixturedata = []
            benchfound = False
            for res in self.fixture:
                if res[0] == resultparams['benchmark_name']:
                    fixturedata = res
                    benchfound = True
                    break
            self.assertTrue(benchfound)
            # get correct result value depending on the type of result
            fixturevalue = 0
            if fixturedata[1] == "SimpleComparisonResult":
                fixturevalue = fixturedata[2]['changed_time']
            else:
                fixturevalue = fixturedata[2]['avg_changed']
            self.assertEqual(resultparams['result_value'], fixturevalue)

if __name__ == "__main__":
    unittest.main()
