from django.db import connection, reset_queries


class SQLCountMiddleware(object):
    def process_request(self, request):
        reset_queries()

    def process_response(self, request, response):
        for i in connection.queries:
            print(i['sql'])
        print('本次视图{0}请求处理{1}条SQL'.format(request.get_full_path(),len(connection.queries)))
        return response