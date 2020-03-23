from django.conf.urls import url
from datacenter.views import *

urlpatterns = [
    url(r'^$', index, {'funid': '2'}),
    url(r'^test/$', test),
    url(r'^processindex/(\d+)/$', processindex),
    url(r'^index/$', index, {'funid': '2'}),
    url(r'^get_process_rto/$', get_process_rto),
    url(r'^get_daily_processrun/$', get_daily_processrun),
    url(r'^get_process_index_data/$', get_process_index_data),

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
    url(r'^create_process/$', create_process),
    url(r'^process_run/$', process_run),
    url(r'^process_destroy/$', process_destroy),
    url(r'^get_process_monitor_tree/$', get_process_monitor_tree),
    url(r'^pm_target_data/$', pm_target_data),
    url(r'^get_exception_data/$', get_exception_data),
    url(r'^get_log_info/$', get_log_info),
    url(r'^target_test/$', target_test),
    url(r'^supplement_process/$', supplement_process),

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
    url(r'^reporting_save/$', reporting_save),
    url(r'^reporting_new/$', reporting_new),
    url(r'^reporting_recalculate/$', reporting_recalculate),
    url(r'^reporting_reextract/$', reporting_reextract),
    url(r'^reporting_formulacalculate/$', reporting_formulacalculate),

    # 报表上报
    url(r'^report_submit/(?P<funid>\d+)/$', report_submit_index),
    url(r'^report_submit_data/$', report_submit_data),
    url(r'^report_submit_save/$', report_submit_save),
    url(r'^report_submit_del/$', report_submit_del),

    # 场景管理
    url(r'^scene/$', scene, {'funid': '70'}),
    url(r'^scenedel/$', scenedel),
    url(r'^scenemove/$', scenemove),

    # 预案管理
    url(r'^script/$', script, {'funid': '32'}),
    url(r'^scriptdata/$', scriptdata),
    url(r'^scriptdel/$', scriptdel),
    url(r'^scriptsave/$', scriptsave),
    url(r'^scriptexport/$', scriptexport),
    url(r'^processconfig/$', processconfig, {'funid': '31'}),
    url(r'^processscriptsave/$', processscriptsave),
    url(r'^get_script_data/$', get_script_data),
    url(r'^remove_script/$', remove_script),
    url(r'^setpsave/$', setpsave),
    url(r'^custom_step_tree/$', custom_step_tree),
    url(r'^processconfig/$', processconfig, {'funid': '63'}),
    url(r'^del_step/$', del_step),
    url(r'^move_step/$', move_step),
    url(r'^get_all_groups/$', get_all_groups),
    url(r'^processdesign/$', process_design, {"funid": "33"}),
    url(r'^process_data/$', process_data),
    url(r'^process_save/$', process_save),
    url(r'^process_del/$', process_del),
    url(r'^verify_items_save/$', verify_items_save),
    url(r'^get_verify_items_data/$', get_verify_items_data),
    url(r'^remove_verify_item/$', remove_verify_item),
    # *************************add
    url(r'^processdraw/(\d+)/$', processdraw, {'funid': '67'}),
    url(r'^getprocess/$', getprocess),
    url(r'^processdrawsave/$', processdrawsave),
    url(r'^processdrawrelease/$', processdrawrelease),
    url(r'^processdrawtest/$', processdrawtest),
    url(r'^processcopy/$', processcopy),

    # 切换演练
    url(r'^falconstorswitch/(?P<process_id>\d+)$', falconstorswitch),
    url(r'^falconstorswitchdata/$', falconstorswitchdata),
    url(r'^falconstorrun/$', falconstorrun),
    url(r'^falconstor/(\d+)/$', falconstor, {'funid': '49'}),
    url(r'^save_invitation/$', save_invitation),
    url(r'^falconstor_run_invited/$', falconstor_run_invited),
    url(r'^fill_with_invitation/$', fill_with_invitation),
    url(r'^save_modify_invitation/$', save_modify_invitation),

    url(r'^getrunsetps/$', getrunsetps),
    url(r'^falconstorcontinue/$', falconstorcontinue),
    url(r'^processsignsave/$', processsignsave),
    url(r'^get_current_scriptinfo/$', get_current_scriptinfo),
    url(r'^ignore_current_script/$', ignore_current_script),
    url(r'^stop_current_process/$', stop_current_process),
    url(r'^verify_items/$', verify_items),
    url(r'^show_result/$', show_result),
    url(r'^reject_invited/$', reject_invited),
    url(r'^reload_task_nums/$', reload_task_nums),
    url(r'^delete_current_process_run/$', delete_current_process_run),
    url(r'^get_celery_tasks_info/$', get_celery_tasks_info),
    url(r'^revoke_current_task/$', revoke_current_task),
    url(r'^get_script_log/$', get_script_log),
    url(r'^save_task_remark/$', save_task_remark),
    url(r'^get_server_time_very_second/$', get_server_time_very_second),

    # 历史查询
    url(r'^custom_pdf_report/$', custom_pdf_report),
    url(r'^falconstorsearch/$', falconstorsearch, {'funid': '64'}),
    url(r'^falconstorsearchdata/$', falconstorsearchdata),
    url(r'^tasksearch/$', tasksearch, {'funid': '65'}),
    url(r'^tasksearchdata/$', tasksearchdata),

    # 其他
    url(r'^downloadlist/$', downloadlist, {'funid': '7'}),
    url(r'^download/$', download),
    url(r'^download_list_data/$', download_list_data),
    url(r'^knowledge_file_del/$', knowledge_file_del),

    # 邀请
    url(r'^invite/$', invite),
    url(r'^get_all_users/$', get_all_users),

    # 数据服务
    url(r'^datacenter/$', DataCenter.as_view()),

    # 报表服务器
    url(r'^report_server/$', report_server, {'funid': '39'}),
    url(r'^report_server_save/$', report_server_save),
]
