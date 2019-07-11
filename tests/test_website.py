# -*- coding: utf-8 -*-

import unittest
import oss2
from oss2 import to_string

from .common import *
from oss2.models import (ConditionInlcudeHeader, 
                        Condition, 
                        Redirect, 
                        RedirectMirrorHeaders,
                        MirrorHeadersSet, 
                        RoutingRule, 
                        BucketWebsite,
                        REDIRECT_TYPE_MIRROR,
                        REDIRECT_TYPE_EXTERNAL,
                        REDIRECT_TYPE_ALICDN,
                        REDIRECT_TYPE_INTERNAL)


class TestWebsite(OssTestCase):
    
    def test_normal_set_website_without_routing_rule(self):

        key = self.random_key('/')
        content = random_bytes(32)

        self.bucket.put_object('index.html', content)

        # set index_file and error_file
        self.bucket.put_bucket_website(BucketWebsite('index.html', 'error.html'))
        wait_meta_sync()

        def same_website(website, index, error):
            return website.index_file == index and website.error_file == error

        # check index_file and error_file
        self.retry_assert(lambda: same_website(self.bucket.get_bucket_website(), 'index.html', 'error.html'))

        # will be reidrect to inext
        result = self.bucket.get_object(key)
        self.assertEqual(result.read(), content)

        self.bucket.delete_object('index.html')

        # test chinese
        for index, error in [('index+中文.html', 'error.中文'), (u'index+中文.html', u'error.中文')]:
            self.bucket.put_bucket_website(BucketWebsite(index, error))
            self.retry_assert(lambda: same_website(self.bucket.get_bucket_website(), to_string(index), to_string(error)))

        # delete website
        self.bucket.delete_bucket_website()
        self.bucket.delete_bucket_website()

        self.assertRaises(oss2.exceptions.NoSuchWebsite, self.bucket.get_bucket_website)

    def test_normal_set_website_with_mirror(self):

        index_file = 'index.html'
        error_file = 'error.html'

        # rule condition
        include_header1= ConditionInlcudeHeader('host', 'test.oss-cn-beijing-internal.aliyuncs.com')
        include_header2 = ConditionInlcudeHeader('host', 'test.oss-cn-shenzhen-internal.aliyuncs.com')
        condition1 = Condition(key_prefix_equals='1~!@#$%^&*()-_=+|\\[]{}<>,./?`~',
                            http_err_code_return_equals=404, include_header_list=[include_header1, include_header2])
        condition2 = Condition(key_prefix_equals='2~!@#$%^&*()-_=+|\\[]{}<>,./?`~', 
                            http_err_code_return_equals=404, include_header_list=[include_header1, include_header2])

        # rule redirect
        mirror_headers_set_1 = MirrorHeadersSet("myheader-key5","myheader-value5")
        mirror_headers_set_2 = MirrorHeadersSet("myheader-key6","myheader-value6")
        set_list = [mirror_headers_set_1, mirror_headers_set_2]
        pass_list = ['myheader-key1', 'myheader-key2']
        remove_list = ['myheader-key3', 'myheader-key4']
        mirror_header = RedirectMirrorHeaders(pass_all=True, pass_list=pass_list, remove_list=remove_list, set_list=set_list)

        # direct type Mirror
        redirect1 = Redirect(redirect_type='Mirror', mirror_url='http://www.test.com/', mirror_pass_query_string=True, 
                            mirror_follow_redirect=True, mirror_check_md5=False, mirror_headers=mirror_header)
        
        redirect2 = Redirect(redirect_type='Mirror', pass_query_string=False, mirror_url='http://www.test.com/', 
                            mirror_url_slave='http://www.slave.com/', mirror_url_probe='http://www.test.com/index.html', 
                            mirror_pass_query_string=False, mirror_follow_redirect=True, mirror_check_md5=True, 
                            mirror_headers=mirror_header)

        rule1_num = 1
        rule2_num = 2
        rule1 = RoutingRule(rule1_num, condition=condition1, redirect=redirect1)
        rule2 = RoutingRule(rule2_num, condition=condition2, redirect=redirect2)
        website_set = BucketWebsite(index_file, error_file, [rule1, rule2])
        self.bucket.put_bucket_website(website_set)
        wait_meta_sync()

        # get websete config
        website_get = self.bucket.get_bucket_website()
        self.assertEqual(website_get.index_file, index_file)
        self.assertEqual(website_get.error_file, error_file)
        self.assertEqual(len(website_get.rules), 2)
        
        for rule in website_get.rules:
            # check rule_num
            self.assertTrue(rule.rule_num in [rule1_num, rule2_num])

            if rule.rule_num == rule1_num:
                cmp_condition = condition1
                cmp_redirect = redirect1
            else:
                cmp_condition = condition2
                cmp_redirect = redirect2

            # check conditon
            t_condition = rule.condition
            self.assertEqual(t_condition.key_prefix_equals, cmp_condition.key_prefix_equals)
            self.assertEqual(t_condition.http_err_code_return_equals, cmp_condition.http_err_code_return_equals)
            self.assertEqual(len(t_condition.include_header_list), len(cmp_condition.include_header_list))

            # check redirect
            t_redirect = rule.redirect
            self.assertEqual(t_redirect.redirect_type, cmp_redirect.redirect_type)   
            # pass_query_string will be coved by mirror_pass_query_string when Mirror reidrect type
            self.assertEqual(t_redirect.pass_query_string, cmp_redirect.mirror_pass_query_string)
            self.assertEqual(t_redirect.mirror_url, cmp_redirect.mirror_url)
            self.assertEqual(t_redirect.mirror_url_slave, cmp_redirect.mirror_url_slave)
            self.assertEqual(t_redirect.mirror_url_probe, cmp_redirect.mirror_url_probe)
            self.assertEqual(t_redirect.mirror_pass_query_string, cmp_redirect.mirror_pass_query_string)
            self.assertEqual(t_redirect.mirror_follow_redirect, cmp_redirect.mirror_follow_redirect)   
            self.assertEqual(t_redirect.mirror_check_md5, cmp_redirect.mirror_check_md5)

            #check redirect mirror_headers
            t_mirror_headers = t_redirect.mirror_headers
            cmp_mirror_headers = cmp_redirect.mirror_headers
            self.assertEqual(t_mirror_headers.pass_all, cmp_mirror_headers.pass_all)
            self.assertEqual(len(t_mirror_headers.pass_list), len(cmp_mirror_headers.pass_list))
            self.assertEqual(len(t_mirror_headers.remove_list), len(cmp_mirror_headers.remove_list))
            self.assertEqual(len(t_mirror_headers.set_list), len(cmp_mirror_headers.set_list))

            self.bucket.delete_bucket_website()  

    def test_normal_set_website_with_alicdn_external_internal(self):
        index_file = 'index.html'
        error_file = 'error.html'

        include_header1= ConditionInlcudeHeader('host', 'test.oss-cn-beijing-internal.aliyuncs.com')
        include_header2 = ConditionInlcudeHeader('host', 'test.oss-cn-shenzhen-internal.aliyuncs.com')
        condition1 = Condition(key_prefix_equals='1~!@#$%^&*()-_=+|\\[]{}<>,./?`~', 
                            http_err_code_return_equals=404, include_header_list=[include_header1, include_header2])
        condition2 = Condition(key_prefix_equals='2~!@#$%^&*()-_=+|\\[]{}<>,./?`~',
                            http_err_code_return_equals=404, include_header_list=[include_header1, include_header2])
        condition3 = Condition(key_prefix_equals='3~!@#$%^&*()-_=+|\\[]{}<>,./?`~', 
                            http_err_code_return_equals=404, include_header_list=[include_header1, include_header2])

        # test direct type AliCDN 
        redirect1 = Redirect(redirect_type=REDIRECT_TYPE_ALICDN, pass_query_string=True, replace_key_with='${key}.suffix', 
                            proto='http', host_name='oss.aliyuncs.com', http_redirect_code=302)

        # test direct type  External
        redirect2 = Redirect(redirect_type=REDIRECT_TYPE_EXTERNAL, pass_query_string=False, replace_key_prefix_with='abc',
                            proto='https', host_name='oss.aliyuncs.com', http_redirect_code=302)

        # test direct type  Internal
        redirect3 = Redirect(redirect_type=REDIRECT_TYPE_INTERNAL, pass_query_string=False, replace_key_with='${key}.suffix')

        rule1_num = 1
        rule2_num = 2
        rule3_num = 3
        rule1 = RoutingRule(rule1_num, condition=condition1, redirect=redirect1)
        rule2 = RoutingRule(rule2_num, condition=condition2, redirect=redirect2)
        rule3 = RoutingRule(rule3_num, condition=condition3, redirect=redirect3)
        website_set = BucketWebsite(index_file, error_file, [rule1, rule2, rule3])
        self.bucket.put_bucket_website(website_set)
        wait_meta_sync()

        website_get = self.bucket.get_bucket_website()
        self.assertEqual(website_get.index_file, index_file)
        self.assertEqual(website_get.error_file, error_file)
        self.assertEqual(len(website_get.rules), 3)

        for rule in website_get.rules:
            # check rule_num
            self.assertTrue(rule.rule_num in [rule1_num, rule2_num, rule3_num])

            if rule.rule_num == rule1_num:
                cmp_condition = condition1
                cmp_redirect = redirect1
            elif rule.rule_num == rule2_num:
                cmp_condition = condition2
                cmp_redirect = redirect2
            else:
                cmp_condition = condition3
                cmp_redirect = redirect3

            # check conditon
            t_condition = rule.condition
            self.assertEqual(t_condition.key_prefix_equals, cmp_condition.key_prefix_equals)
            self.assertEqual(t_condition.http_err_code_return_equals, cmp_condition.http_err_code_return_equals)
            self.assertEqual(len(t_condition.include_header_list), len(cmp_condition.include_header_list))

            # check redirect
            t_redirect = rule.redirect
            self.assertEqual(t_redirect.redirect_type, cmp_redirect.redirect_type)
            self.assertEqual(t_redirect.pass_query_string, cmp_redirect.pass_query_string) 
            self.assertEqual(t_redirect.replace_key_with, cmp_redirect.replace_key_with)   
            self.assertEqual(t_redirect.replace_key_prefix_with, cmp_redirect.replace_key_prefix_with)  
            self.assertEqual(t_redirect.proto, cmp_redirect.proto)   
            self.assertEqual(t_redirect.host_name, cmp_redirect.host_name)   
            self.assertEqual(t_redirect.http_redirect_code, cmp_redirect.http_redirect_code)   
            self.bucket.delete_bucket_website()

    def test_unnormal_routing_rule(self):
        index_file = 'index.html'
        error_file = 'error.html'

        # correct test
        # correct condition
        include_header1= ConditionInlcudeHeader('host', 'test.oss-cn-beijing-internal.aliyuncs.com')
        include_header2 = ConditionInlcudeHeader('host', 'test.oss-cn-shenzhen-internal.aliyuncs.com')
        condition = Condition(key_prefix_equals='~!@#$%^&*()-_=+|\\[]{}<>,./?`~', 
                            http_err_code_return_equals=404, include_header_list=[include_header1, include_header2])

        # correct redirect
        redirect = Redirect(redirect_type=REDIRECT_TYPE_MIRROR, mirror_url='http://www.test.com/', mirror_pass_query_string=True, 
                        mirror_follow_redirect=True, mirror_check_md5=False, mirror_headers=None)

        # correct routing rules 
        rule_num = 1
        rule = RoutingRule(rule_num, condition=condition, redirect=redirect)
        website_set = BucketWebsite(index_file, error_file, [rule])

        # correct set get delete function
        self.bucket.put_bucket_website(website_set)
        wait_meta_sync()
        website_get = self.bucket.get_bucket_website()
        self.bucket.delete_bucket_website()

        # start incorrect test
        # rule_num type is not int
        self.assertRaises(oss2.exceptions.ClientError, RoutingRule, rule_num='str', condition=condition, redirect=redirect)
        
        # rule_num < 0
        self.assertRaises(oss2.exceptions.ClientError, RoutingRule, rule_num=-1, condition=condition, redirect=redirect)

        # rule_num is none
        self.assertRaises(oss2.exceptions.ClientError, RoutingRule, rule_num=None, condition=condition, redirect=redirect)

        # condition is none
        self.assertRaises(oss2.exceptions.ClientError, RoutingRule, rule_num=1, condition=None, redirect=redirect)
        
        # redirect is none
        self.assertRaises(oss2.exceptions.ClientError, RoutingRule, rule_num=1, condition=condition, redirect=None)

        # condition.http_err_code_return_equals is not 404 when reidrect type is mirror
        t_condition = Condition(key_prefix_equals='~!@#$%^&*()-_=+|\\[]{}<>,./?`~',
                            http_err_code_return_equals=400, include_header_list=[include_header1, include_header2])
        self.assertRaises(oss2.exceptions.ClientError, RoutingRule, rule_num=1, condition=t_condition, redirect=redirect)

        # rules type is not list
        self.assertRaises(oss2.exceptions.ClientError, BucketWebsite, index_file, error_file, rule)
        
        # rules capacity > 5
        self.assertRaises(oss2.exceptions.ClientError, BucketWebsite, index_file, error_file, [rule, rule, rule, rule, rule, rule])

    def test_unnormal_rule_conditon(self):

        # correct condition
        include_header1= ConditionInlcudeHeader('host', 'test.oss-cn-beijing-internal.aliyuncs.com')
        include_header2 = ConditionInlcudeHeader('host', 'test.oss-cn-shenzhen-internal.aliyuncs.com')
        condition = Condition(key_prefix_equals='test',http_err_code_return_equals=404, include_header_list=[include_header1, include_header2])

        # start incorrect conditon test
        # condition include_header_list type is not list
        self.assertRaises(oss2.exceptions.ClientError, Condition, 'test',404, 'str')
        
        # condition include_header_list capacity >5
        self.assertRaises(oss2.exceptions.ClientError, Condition, 'test', 404, 
                        [include_header1, include_header1, include_header1, include_header1, include_header1, include_header1])

    def test_unnormal_redirect_mirror(self):
    
        index_file = 'index.html'
        error_file = 'error.html'

        # correct test
        # correct condition
        include_header1= ConditionInlcudeHeader('host', 'test.oss-cn-beijing-internal.aliyuncs.com')
        include_header2 = ConditionInlcudeHeader('host', 'test.oss-cn-shenzhen-internal.aliyuncs.com')
        condition1 = Condition(key_prefix_equals='1~!@#$%^&*()-_=+|\\[]{}<>,./?`~', 
                            http_err_code_return_equals=404, include_header_list=[include_header1, include_header2])
        condition2 = Condition(key_prefix_equals='2~!@#$%^&*()-_=+|\\[]{}<>,./?`~', 
                            http_err_code_return_equals=404, include_header_list=[include_header1, include_header2])

        # correct redirect
        # mirro_url_slave is indicated
        redirect1 = Redirect(redirect_type=REDIRECT_TYPE_MIRROR, mirror_url='http://www.test.com/',
                            mirror_url_slave='https://www.slave.com/', mirror_url_probe='http://www.test.com/index.html', 
                            mirror_pass_query_string=True, mirror_follow_redirect=True, mirror_check_md5=False) 

        # mirro_url_slave is not indicated
        redirect2 = Redirect(redirect_type=REDIRECT_TYPE_MIRROR, mirror_url='http://www.test.com/',
                            mirror_pass_query_string=True, mirror_follow_redirect=True, mirror_check_md5=False)

        # correct routing rule
        rule = RoutingRule(rule_num=1, condition=condition1, redirect=redirect1)
        rule = RoutingRule(rule_num=2, condition=condition2, redirect=redirect2)
        website_set = BucketWebsite(index_file, error_file, [rule])

        # correct set & get & delete function 
        self.bucket.put_bucket_website(website_set)
        wait_meta_sync()
        website_get = self.bucket.get_bucket_website()
        self.bucket.delete_bucket_website()

        # start incorrect test        
        # invalid redirect type
        self.assertRaises(oss2.exceptions.ClientError, Redirect,
                        redirect_type='unnormal-direct-type', mirror_url='http://www.test.com/', mirror_pass_query_string=True, 
                        mirror_follow_redirect=True, mirror_check_md5=False)

        # mirror_url not startwith 'http' or 'htttps'
        self.assertRaises(oss2.exceptions.ClientError, Redirect, 
                        redirect_type=REDIRECT_TYPE_MIRROR, mirror_url='www.test.com/', 
                        mirror_pass_query_string=True, mirror_follow_redirect=True, mirror_check_md5=False)

        # mirror_url not endwith '/'                  
        self.assertRaises(oss2.exceptions.ClientError, Redirect, 
                        redirect_type=REDIRECT_TYPE_MIRROR, mirror_url='http://www.test.com', 
                        mirror_pass_query_string=True, mirror_follow_redirect=True, mirror_check_md5=False)

        # mirror_url_slave not startwith 'http' or 'htttps'
        self.assertRaises(oss2.exceptions.ClientError, Redirect, 
                        redirect_type=REDIRECT_TYPE_MIRROR, mirror_url='http://www.test.com/', 
                        mirror_url_slave='www.slave.com/', mirror_url_probe='http://www.test.com/index.html',
                        mirror_pass_query_string=True, mirror_follow_redirect=True, mirror_check_md5=False)

        # mirror_url_slave not endwith '/'             
        self.assertRaises(oss2.exceptions.ClientError, Redirect, 
                        redirect_type=REDIRECT_TYPE_MIRROR, mirror_url='http://www.test.com/', 
                        mirror_url_slave='https://www.slave.com', mirror_url_probe='http://www.test.com/index.html',
                        mirror_pass_query_string=True, mirror_follow_redirect=True, mirror_check_md5=False)

        # mirror_url_probe is none when mirror_url_slave is diticated            
        self.assertRaises(oss2.exceptions.ClientError, Redirect, 
                        redirect_type=REDIRECT_TYPE_MIRROR, mirror_url='http://www.test.com/', 
                        mirror_url_slave='https://www.slave.com/', mirror_url_probe=None,
                        mirror_pass_query_string=True, mirror_follow_redirect=True, mirror_check_md5=False)

        # proto is not empty when reidrect type is mirrorr
        self.assertRaises(oss2.exceptions.ClientError, Redirect, 
                        redirect_type=REDIRECT_TYPE_MIRROR, proto='http', mirror_url='http://www.test.com/', 
                        mirror_pass_query_string=True, mirror_follow_redirect=True, mirror_check_md5=False)

        # host_name is not empty when reidrect type is mirrorr
        self.assertRaises(oss2.exceptions.ClientError, Redirect, 
                        redirect_type=REDIRECT_TYPE_MIRROR, host_name='oss.aliyuncs.com', mirror_url='http://www.test.com/', 
                        mirror_pass_query_string=True, mirror_follow_redirect=True, mirror_check_md5=False)

        #replace_key_prefix_with is not empty when reidrect type is mirrorr
        self.assertRaises(oss2.exceptions.ClientError, Redirect, 
                        redirect_type=REDIRECT_TYPE_MIRROR, replace_key_prefix_with='abc',mirror_url='http://www.test.com/',
                        mirror_pass_query_string=True, mirror_follow_redirect=True, mirror_check_md5=False)

        # http_redirect_code is not empty when reidrect type is mirrorr
        self.assertRaises(oss2.exceptions.ClientError, Redirect, 
                        redirect_type=REDIRECT_TYPE_MIRROR, http_redirect_code=302, mirror_url='http://www.test.com/', 
                        mirror_pass_query_string=True, mirror_follow_redirect=True, mirror_check_md5=False)   

        # correct pass_list
        mirror_header = RedirectMirrorHeaders(pass_list=['a','b'])
        # pass_list type is not list
        self.assertRaises(oss2.exceptions.ClientError, RedirectMirrorHeaders, pass_list='a')
        # pass_list capacity > 10
        pass_list = ['key1', 'key2', 'key3', 'key4', 'key5', 'key6', 'key7', 'key8', 'key9', 'key10', 'key11']
        self.assertRaises(oss2.exceptions.ClientError, RedirectMirrorHeaders, pass_list=pass_list)

        # correct remove_list
        mirror_header = RedirectMirrorHeaders(remove_list=['a','b'])
        # remove_list type is not list
        self.assertRaises(oss2.exceptions.ClientError, RedirectMirrorHeaders, remove_list='str')
        # remove_list capacity > 10
        remove_list = ['key1', 'key2', 'key3', 'key4', 'key5', 'key6', 'key7', 'key8', 'key9', 'key10', 'key11']
        self.assertRaises(oss2.exceptions.ClientError, RedirectMirrorHeaders, remove_list=remove_list)

        # correct set_list
        t_set = MirrorHeadersSet('key1', 'value1')
        mirror_header = RedirectMirrorHeaders(set_list=[t_set])
        # mirror_header set_list type is not list
        self.assertRaises(oss2.exceptions.ClientError, RedirectMirrorHeaders, set_list=t_set)
        # mirror_header set_list capacity > 10
        set_list = [t_set, t_set, t_set, t_set, t_set, t_set, t_set, t_set, t_set, t_set, t_set]
        self.assertRaises(oss2.exceptions.ClientError, RedirectMirrorHeaders, set_list=set_list)

    def test_unnormal_redirect_alicdn_external_internal(self):
        index_file = 'index.html'
        error_file = 'error.html'

        # correct test
        # correct condition
        include_header1= ConditionInlcudeHeader('host', 'test.oss-cn-beijing-internal.aliyuncs.com')
        include_header2 = ConditionInlcudeHeader('host', 'test.oss-cn-shenzhen-internal.aliyuncs.com')
        condition1 = Condition(key_prefix_equals='1~!@#$%^&*()-_=+|\\[]{}<>,./?`~', 
                            http_err_code_return_equals=404, include_header_list=[include_header1, include_header2])
        condition2 = Condition(key_prefix_equals='2~!@#$%^&*()-_=+|\\[]{}<>,./?`~', 
                            http_err_code_return_equals=404, include_header_list=[include_header1, include_header2])
        condition3 = Condition(key_prefix_equals='3~!@#$%^&*()-_=+|\\[]{}<>,./?`~', 
                            http_err_code_return_equals=404, include_header_list=[include_header1, include_header2])

        # correct reidrect AliCDN 
        redirect1 = Redirect(redirect_type=REDIRECT_TYPE_ALICDN, pass_query_string=True, proto='http', 
                            replace_key_with='${key}.suffix', host_name='oss.aliyuncs.com', http_redirect_code=302)

        # correct reidrect  External
        redirect2 = Redirect(redirect_type=REDIRECT_TYPE_EXTERNAL, pass_query_string=False, proto='https', 
                            replace_key_prefix_with='abc', host_name='oss.aliyuncs.com', http_redirect_code=302)

        # correct reidrect  Internal
        redirect3 = Redirect(redirect_type=REDIRECT_TYPE_INTERNAL, pass_query_string=False, replace_key_with='${key}.suffix')

        # correct rules
        rule1 = RoutingRule(rule_num=1, condition=condition1, redirect=redirect1)
        rule2 = RoutingRule(rule_num=2, condition=condition2, redirect=redirect2)
        rule3 = RoutingRule(rule_num=3, condition=condition3, redirect=redirect3)

        # correct website set get and delete function
        website_set = BucketWebsite(index_file, error_file, [rule1, rule2, rule3])
        self.bucket.put_bucket_website(website_set)
        wait_meta_sync()
        website_get = self.bucket.get_bucket_website()
        self.bucket.delete_bucket_website()

        # start incorrect test
        # http_redirect_code < 300
        self.assertRaises(oss2.exceptions.ClientError, Redirect, 
                        redirect_type=REDIRECT_TYPE_ALICDN, pass_query_string=True, replace_key_with='${key}.suffix', proto='http', 
                        host_name='oss.aliyuncs.com', http_redirect_code=299)

        # http_redirect_code > 399
        self.assertRaises(oss2.exceptions.ClientError, Redirect, 
                        redirect_type=REDIRECT_TYPE_ALICDN, pass_query_string=True, replace_key_with='${key}.suffix', proto='http',  
                        host_name='oss.aliyuncs.com', http_redirect_code=400)     

        # replace_key_with and replace_key_prefix_with both is exsit
        self.assertRaises(oss2.exceptions.ClientError, Redirect, 
                        redirect_type=REDIRECT_TYPE_ALICDN, pass_query_string=True, replace_key_with='${key}.suffix', proto='http', 
                        host_name='oss.aliyuncs.com', replace_key_prefix_with='abc', http_redirect_code=302)

        # host_name is not empty when reidirect type is Internal
        self.assertRaises(oss2.exceptions.ClientError,Redirect,
                        redirect_type=REDIRECT_TYPE_INTERNAL, pass_query_string=False, replace_key_with='${key}.suffix', host_name='oss.aliyuncs.com')

        # proto is not empty when redirect type is Internal
        self.assertRaises(oss2.exceptions.ClientError,Redirect,
                        redirect_type=REDIRECT_TYPE_INTERNAL, pass_query_string=False, replace_key_with='${key}.suffix', proto='http')

        # http_redirect_code is not empty when reidirect type is Internal
        self.assertRaises(oss2.exceptions.ClientError,Redirect,
                        redirect_type=REDIRECT_TYPE_INTERNAL, pass_query_string=False, replace_key_with='${key}.suffix', http_redirect_code=302)


if __name__ == '__main__':
    unittest.main()