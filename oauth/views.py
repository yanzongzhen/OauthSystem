#coding:utf-8
# @Time    : 2018/6/5 下午6:47
# @Author  : yanzongzhen
# @Email   : yanzz@catial.cn
# @File    : views.py
# @Software: PyCharm
import json

import os
from flask import request, jsonify, render_template, redirect, session
import logging
import settings
from libs.json_file.json_file_lib import json_file_redaer, json_write
from libs.rewrite.rewrite_utils import myredirect
from home.views import current_user
from libs.auth_code_lib.auth_code_lib import gen_auth_code, verify_auth_code
from libs.auth_token_lib.auth_token_lib import gen_token_return
from models.client import Client
from models.user import User
from oauth import oauth
_redirect_url = None
grant = None

# log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),'oauth2.log')
log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'oauth2.log')
logging.basicConfig(filename=log_path, level=logging.DEBUG, format=settings.LOG_FORMAT, datefmt=settings.DATE_FORMAT)
save_json = json_file_redaer()


@oauth.route('/token', methods=['GET','POST'])
def oauth_token():
    global save_json
    if request.method == 'GET':
        return jsonify(code=1,msg='Not support GET methods')
    else:
        data = request.values
        # data = json.loads(request.data.decode())
        print('values param is %s' % request.values)
        res = verify_auth_code(data)
        if res.get('code') == 1:
            return jsonify(error="001",error_description=res.get('msg'))
        else:
            response = gen_token_return(data)
            if response.get('code') == 1:
                return jsonify(error="001", error_description=response.get('msg'))
            else:
                res_Data = response.get('data')
                return jsonify(access_token=res_Data.access_token,
                               refresh_token=res_Data.refresh_token,
                               expires_in=res_Data.expires_in)


@oauth.route('/authorize', methods=['GET', 'POST'])
def authorize():
    global grant
    global _redirect_url
    user = current_user()
    if request.method == 'GET':
        request_data = request.args
        client_id = request_data.get('client_id')
        redirect_url = request_data.get('redirect_uri')
        raw_redirect_url = redirect_url.split('?')[0]
        _token = request_data.get('token')
        _state = request_data.get('state')
        _redirect_url = redirect_url+'&token=%s&state=%s' % (_token, _state)
        response_type = request_data.get('response_type')
        grant = Client.select().filter(Client.client_id == client_id).first()
        if grant:
            if grant.response_type != response_type:
                return jsonify(code=1,msg='Not support response_type')
            else:
                if raw_redirect_url == grant.redirect_uri:
                    back_uri = settings.HOST + '/oauth/authorize?' \
                                               'redirect_uri=%s&client_id=%s' \
                                               '&response_type=%s&state=%s' % (
                                                redirect_url,
                                                client_id,
                                                response_type,
                                                _state
                                                )
                    print('\r\n**************back_uri**************\r\n')
                    print(back_uri)
                    print('\r\n**************back_uri**************\r\n')
                    return render_template('authrized.html', grant=grant, user=user, back_uri=back_uri)
                else:
                    return jsonify(code=1,msg='incorrect redirect_uri')
        else:
            return jsonify(code=1,msg='grant Not such client')
    else:
        if request.form['confirm'] == 'Submit':
            uri = gen_auth_code(grant=grant, redirect_uri=_redirect_url,grant_user=user)
            return myredirect(uri)
        else:
            return jsonify(code=1,msg='Client give up')


@oauth.route('/login', methods=['GET', 'POST'])
def auth_login():
    if request.method == 'POST':
        user = request.form['user']
        pw = request.form['pw']
        back_uri = request.form['back_uri']
        user_tmp = User.select().filter(User.username == user).first()
        if user_tmp:
            if user_tmp.check_password(pw):
                session['id'] = user_tmp.id
                return redirect(back_uri)
            else:
                return '密码错误'
        return '还未注册'
