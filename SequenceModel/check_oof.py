import os
import pandas as pd
import numpy as np
from sklearn.metrics import log_loss
import pandas as pd
import os
from settings import *

def mutl_log_loss(y_truth,y_pre):
    y_tre_tmp=y_truth[:,0]
    y_pre_tmp=y_pre[:,0]
    tmp_loss=log_loss(y_tre_tmp, y_pre_tmp,labels=[0,1])
    return tmp_loss

if not os.path.exists('standard_test.csv'):
    tmp = pd.read_csv('stage_2_sample_submission.csv')
    tmp['filename'] = tmp['ID'].apply(lambda st: "ID_" + st.split('_')[1])
    tmp['type'] = tmp['ID'].apply(lambda st: st.split('_')[2])
    pivot_df = tmp[['Label', 'filename', 'type']].drop_duplicates().pivot(index='filename', columns='type', values='Label').reset_index()
    pivot_df.to_csv(r'standard_test.csv',index=False)

if not os.path.exists('standrad.csv'):
    tmp = pd.read_csv(train_csv)
    tmp['filename'] = tmp['ID'].apply(lambda st: "ID_" + st.split('_')[1])
    tmp['type'] = tmp['ID'].apply(lambda st: st.split('_')[2])
    pivot_df = tmp[['Label', 'filename', 'type']].drop_duplicates().pivot(index='filename', columns='type', values='Label').reset_index()
    pivot_df.to_csv(r'standard.csv',index=False)

train = r'./standard.csv'
train_df = pd.read_csv(train)
train_df["filename"] = [tmp.replace('.dcm', '') for tmp in train_df["filename"]]
train_df["filename"] = [tmp.replace('.png', '') for tmp in train_df["filename"]]
train_ids = train_df['filename']

test = r'./standard_test.csv'
test_df = pd.read_csv(test)
test_df["filename"] = [tmp.replace('.dcm', '') for tmp in test_df["filename"]]
test_df["filename"] = [tmp.replace('.png', '') for tmp in test_df["filename"]]
test_ids = test_df['filename']

train_num = len(train_ids)
test_num = len(test_ids)

def get_train_dict():
    dict_tmp = {}
    i = 0
    for id in train_ids:
        dict_tmp[id] = i
        i += 1
    return dict_tmp

def get_test_dict():
    dict_tmp = {}
    i = 0
    for id in test_ids:
        dict_tmp[id] = i
        i += 1
    return dict_tmp
#==========================================================================================================
if 1:
    def get_predict(df):
        types = ['any', 'epidural', 'intraparenchymal', 'intraventricular', 'subarachnoid', 'subdural']
        predict_list = []

        for type in types:
            predict = np.asarray(list(df[type + '_y'])).reshape([-1, 1])
            predict_list.append(predict)

        predict = np.concatenate(predict_list,axis =1)
        return predict

    def get_train_test_predict(dir):
        model_name = os.path.split(dir)[1]
        train = r'./standard.csv'
        train_df = pd.read_csv(train)

        pd_tmp = os.path.join(dir,model_name+'_val_prob_TTA_stage2_finetune.csv')
        if not os.path.exists(pd_tmp):
            pd_tmp = os.path.join(dir, model_name + '_val_prob_TTA.csv')

        if not os.path.exists(pd_tmp):
            return None,None

        print(pd_tmp)
        pd_tmp_df = pd.read_csv(pd_tmp)
        train_df["filename"] =[ tmp.replace('.dcm','') for tmp in train_df["filename"]]
        pd_tmp_df["filename"] =[ tmp.replace('.png','') for tmp in pd_tmp_df["filename"]]
        pd_tmp_df["filename"] =[ tmp.replace('.dcm','') for tmp in pd_tmp_df["filename"]]

        merge_csv = pd.merge(train_df, pd_tmp_df, how='left', on='filename')
        merge_csv.to_csv(os.path.join(dir, 'DEBUG_'+model_name + '_val_stage2_sample.csv'))
        predict = get_predict(merge_csv)

        train = r'./standard_test.csv'
        train_df = pd.read_csv(train)

        pd_tmp = os.path.join(dir,model_name+'_test_prob_TTA_stage2_finetune.csv')

        if not os.path.exists(pd_tmp):
            pd_tmp = os.path.join(dir, model_name + '_test_prob_TTA_stage2.csv')

        if not os.path.exists(pd_tmp):
            print(' test None')
            return predict, np.zeros([test_num, 6, 1])

        print(pd_tmp)
        pd_tmp_df = pd.read_csv(pd_tmp)
        train_df["filename"] = [tmp.replace('.dcm', '') for tmp in train_df["filename"]]
        pd_tmp_df["filename"] = [tmp.replace('.png', '') for tmp in pd_tmp_df["filename"]]
        pd_tmp_df["filename"] = [tmp.replace('.dcm', '') for tmp in pd_tmp_df["filename"]]

        merge_csv = pd.merge(train_df, pd_tmp_df, how='left', on='filename')
        merge_csv.to_csv(os.path.join(dir, 'DEBUG_'+model_name + '_test_stage2_sample.csv'))
        predict_test = get_predict(merge_csv)

        print(predict_test.shape)
        return predict, predict_test

    train_predicts = []
    test_predicts= []

#################################################################################################################
    #============================================================================================================
    # pd_tmp
    for model_name in ['dsn121_256_fine', 'dsn121_512_fine', 'dsn169_256_fine', 'se101_256_fine']:
        print(model_name)
        val_fea, test_fea = get_train_test_predict(dir = os.path.join(feature_path, r'from_yl_all_tta_stage2_finetune', model_name))
        if val_fea is not None:
            train_predicts.append(val_fea)
        if test_fea is not None:
            test_predicts.append(test_fea)

#================================================================================================================

if 1:
    label_list = []
    types = ['any', 'epidural', 'intraparenchymal', 'intraventricular', 'subarachnoid', 'subdural']
    weight = [2.0, 1.0, 1.0, 1.0, 1.0, 1.0]
    loss = 0
    index = 0
    merge_csv = pd.read_csv(r'./standard.csv')
    for w, type in zip(weight, types):
        label = np.asarray(list(merge_csv[type])).reshape([-1, 1])
        label_list.append(label)
    label = np.concatenate(label_list,axis =1)

if 1:
    def get(label, predict):
        weight= [2.0,1.0,1.0,1.0,1.0,1.0]
        loss = 0
        for index in range(6):
            label_tmp = label[:, index].reshape([-1, 1])
            tmp = predict[: , index].reshape([-1, 1])
            loss  += weight[index]*mutl_log_loss(label_tmp, tmp)
            index += 1
        loss /= sum(weight)
        return loss

    for model in train_predicts:
        print(model.shape)
        loss = get(label, model)
        print(loss)


X_list = []
X_test_list = []
for model, model_test in  zip(train_predicts, test_predicts):
    model = model.reshape([train_num, 6, 1])
    model_test = model_test.reshape([test_num, 6, 1])
    X_list.append(model)
    X_test_list.append(model_test)

def move(lst, k):
    return lst[k:] + lst[:k]

def get_X(x_list):
    X = []
    x_mean = np.mean(x_list,axis=0)
    X.append(x_mean)
    x_list_move = move(x_list, 1)
    for x0, x1 in zip(x_list, x_list_move):
        X.append((x0-x1))
    X += x_list
    return X

X_list = get_X(X_list)
X_test_list = get_X(X_test_list)
X = np.concatenate(X_list,axis = 2)
X_test = np.concatenate(X_test_list,axis = 2)
model_num = len(X_list)

y = label
X = X