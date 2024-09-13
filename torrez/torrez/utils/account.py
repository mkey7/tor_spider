from datetime import datetime

import pymongo



# 初始化站点的用户名密码信息
# todo 初始化数据到 redis或者mysql中

def connect_mongo():
    client = pymongo.MongoClient(host=MongoDB['host'], port=MongoDB['port'])
    db = client['DW']
    # db.authenticate("local","123456")
    collection = db['Account']
    return collection


def insert_accounts_to_mongodb(collection):
    collection.delete_many({})
    accounts = [
        # 用户类型：用户名：密码：标签
        ['MGMGrand', 'liyiyi', 'Qazpl,123', '0'],
        ['Cabyc', 'liyiyi', 'Qazpl,123', '0'],
        # ['MGMGrand', 'mgmgrandhaha', 'mgmgrandpass', '0'],
        ['Exploit.IN', 'liyiyi', 'Qazpl,123', '0'],
        ['Exploit.IN', 'liyiyiyi', 'Qazpl,123', '0'],
        ['Torrez', 'wenyan', 'torrezpass', '0'],
        ['Torrez', 'torrezhaha', 'torrezpass', '0'],
        ['Asap', 'wenyan', 'asappass', '0'],
        ['Asap', 'asaphaha', 'asappass', '0'],


    ]
    # 将其插入到account表中
    for account_info in accounts:
        account_data = {
            'type': account_info[0],
            'username': account_info[1],
            'password': account_info[2],
            'label': account_info[3],
            'created_at': datetime.now()
        }
        collection.insert_one(account_data)


def get_account(account_type):
    client = pymongo.MongoClient(host=MongoDB['host'], port=MongoDB['port'])
    db = client['DW']
    collection = db['Account']

    # 选择一个标签为0的账户，并返回其账号用户名和密码，然后将其标签改为1
    account = collection.find_one({'type': account_type, 'label': '0'}, {'username': 1, 'password': 1, '_id': 0})

    if account:
        # 将标签改为1
        # collection.update_one({'type': account_type, 'label': '0'}, {'$set': {'label': '1'}})
        return account
    else:
        return None


def main():
    collection = connect_mongo()
    insert_accounts_to_mongodb(collection)
    account = get_account('MGMGrand')
    print(f"Username: {account['username']}, Password: {account['password']}")

    account2 = get_account('Cabyc')
    print(f"Username: {account2['username']}, Password: {account2['password']}")


if __name__ == "__main__":
    main()
