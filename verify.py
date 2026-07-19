import sys, os
sys.path.insert(0, r"C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2SLbX4G468EhUUaTU5XxvTc\workspace\conv_19f4492d96e_062d7905d35c\output\bibi")
os.chdir(r"C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2SLbX4G468EhUUaTU5XxvTc\workspace\conv_19f4492d96e_062d7905d35c\output\bibi")
from application import app
client = app.test_client()

def check(path):
    resp = client.get(path)
    size = len(resp.data)
    print("{path} -> {code} | size={size} bytes".format(path=path, code=resp.status_code, size=size))
    return resp

print("=== Verification ===")
r = check('/')
html = r.get_data(as_text=True)
print("  contains <script> tag:", '<script' in html)
print("  contains require.js:", '/static/ng-js/libs/require.js' in html)
print("  contains store.css:", '/static/css/store.css' in html)
check('/static/ng-js/main.js')
check('/static/ng-js/controllers/productListCtrl.js')
check('/static/ng-js/views/product-list.html')
check('/static/ng-js/libs/angular.js')
check('/static/ng-js/libs/angular-route.js')
check('/static/ng-js/services/apiService.js')
check('/static/ng-js/views/home.html')
check('/static/ng-js/views/cart.html')
check('/static/ng-js/views/login.html')
check('/static/ng-js/views/checkout.html')
check('/static/css/store.css')
