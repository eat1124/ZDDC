from django.conf.urls import url
from datacenter.views import *

urlpatterns = [
    url(r'^$', index, {'funid': '2'}),
    url(r'^test/$', test),
    url(r'^index/$', index, {'funid': '2'}),

    # 用户登录
    url(r'^login/$', login),
    url(r'^userlogin/$', userlogin),
    url(r'^forgetPassword/$', forgetPassword),
    url(r'^resetpassword/([0-9a-zA-Z]{8}-[0-9a-zA-Z]{4}-[0-9a-zA-Z]{4}-[0-9a-zA-Z]{4}-[0-9a-zA-Z]{12})/$',
        resetpassword),
    url(r'^reset/$', reset),
    url(r'^password/$', password),
    url(r'^userpassword/$', userpassword),

    # 进程管理
    url(r'^process_monitor/$', process_monitor_index, {'funid': '21'}),
    url(r'^process_monitor_data/$', process_monitor_data),
    url(r'^process_run/$', process_run),
    url(r'^get_process_monitor_tree/$', get_process_monitor_tree),
    url(r'^pm_target_data/$', pm_target_data),
    url(r'^get_exception_data/$', get_exception_data),
    url(r'^exception_data_del/$', exception_data_del),
    url(r'^get_log_info/$', get_log_info),
    url(r'^target_test/$', target_test),
    url(r'^supplement_process/$', supplement_process),
    url(r'^get_supplement_process_info/$', get_supplement_process_info),
    url(r'^get_process_monitor_info/$', get_process_monitor_info),

    # 系统维护
    url(r'^organization/$', organization, {'funid': '5'}),
    url(r'^orgdel/$', orgdel),
    url(r'^orgmove/$', orgmove),
    url(r'^orgpassword/$', orgpassword),
    url(r'^group/$', group, {'funid': '6'}),
    url(r'^groupsave/$', groupsave),
    url(r'^groupdel/$', groupdel),
    url(r'^getusertree/$', getusertree),
    url(r'^groupsaveusertree/$', groupsaveusertree),
    url(r'^getfuntree/$', getfuntree),
    url(r'^groupsavefuntree/$', groupsavefuntree),
    url(r'^function/$', function, {'funid': '8'}),
    url(r'^fundel/$', fundel),
    url(r'^funmove/$', funmove),

    # 字典维护
    url(r'^dict/$', dictindex, {'funid': '9'}),
    url(r'^dictsave/$', dictsave),
    url(r'^dictselect/$', dictselect),
    url(r'^dictlistsave/$', dictlistsave),
    url(r'^dictdel/$', dictdel),
    url(r'^dictlistdel/$', dictlistdel),

    # 存储配置
    url(r'^storage/$', storage_index, {'funid': '10'}),
    url(r'^storage_data/$', storage_data),
    url(r'^storage_save/$', storage_save),
    url(r'^storage_del/$', storage_del),

    # 周期配置
    url(r'^cycle/$', cycle_index, {'funid': '11'}),
    url(r'^cycle_data/$', cycle_data),
    url(r'^cycle_save/$', cycle_save),
    url(r'^cycle_del/$', cycle_del),

    # 数据源配置
    url(r'^source/$', source_index, {'funid': '12'}),
    url(r'^get_source_tree/$', get_source_tree),
    url(r'^del_source/$', del_source),
    url(r'^move_source/$', move_source),

    # 应用管理
    url(r'^app/$', app_index, {'funid': '7'}),
    url(r'^app_data/$', app_data),
    url(r'^app_save/$', app_save),
    url(r'^app_del/$', app_del),

    # 指标管理
    url(r'^target/$', target_index, {'funid': '13'}),
    url(r'^target_data/$', target_data),
    url(r'^target_formula_data/$', target_formula_data),
    url(r'^target_save/$', target_save),
    url(r'^target_del/$', target_del),
    url(r'^load_weight_targets/$', load_weight_targets),

    # 应用指标管理
    url(r'^target_app/(?P<funid>\d+)/$', target_app_index),
    url(r'^target_importadminapp/$', target_importadminapp),
    url(r'^target_app_search/(?P<funid>\d+)/$', target_app_search_index),
    url(r'^target_importapp/$', target_importapp),
    url(r'^target_app_del/$', target_app_del),

    # 常数维护
    url(r'^constant/$', constant_index, {'funid': '39'}),
    url(r'^constant_data/$', constant_data),
    url(r'^constant_save/$', constant_save),
    url(r'^constant_del/$', constant_del),

    # 应用常数维护
    url(r'^constant_app/(?P<funid>\d+)/$', constant_app_index),

    # 报表模板管理
    url(r'^report/$', report_index, {'funid': '14'}),
    url(r'^report_data/$', report_data),
    url(r'^report_del/$', report_del),
    url(r'^download_file/$', download_file),

    # 应用报表模板管理
    url(r'^report_app/(?P<funid>\d+)/$', report_app_index),

    # 应用填报
    url(r'^reporting/(?P<cycletype>\d+)/(?P<funid>\d+)/$', reporting_index),
    url(r'^reporting_data/$', reporting_data),
    url(r'^reporting_search_data/$', reporting_search_data),
    url(r'^reporting_del/$', reporting_del),
    url(r'^reporting_release/$', reporting_release),
    url(r'^reporting_save/$', reporting_save),
    url(r'^reporting_new/$', reporting_new),
    url(r'^reporting_recalculate/$', reporting_recalculate),
    url(r'^reporting_reextract/$', reporting_reextract),
    url(r'^reporting_formulacalculate/$', reporting_formulacalculate),
    url(r'^ajax_cumulate/$', ajax_cumulate),

    # 报表上报
    url(r'^report_submit/(?P<funid>\d+)/$', report_submit_index),
    url(r'^report_submit_data/$', report_submit_data),
    url(r'^report_submit_save/$', report_submit_save),
    url(r'^report_submit_del/$', report_submit_del),


    # 数据服务
    url(r'^datacenter/$', DataCenter.as_view()),

    # 报表服务器
    url(r'^report_server/$', report_server, {'funid': '60'}),
    url(r'^report_server_save/$', report_server_save),

    # 首页
    url(r'^get_reporting_log/$', get_reporting_log),
]
