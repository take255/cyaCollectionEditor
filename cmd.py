import bpy
from bpy.types import (PropertyGroup , UIList , Operator)
import imp

from . import utils
imp.reload(utils)

#-------------------------------------------------------
def getprop():
    prop = bpy.context.scene.cyacollectioneditor_oa
    ui_list = bpy.context.window_manager.cyacollectioneditor_list
    itemlist = ui_list.itemlist

    return prop,ui_list,itemlist

Selected_Collection =''
#-------------------------------------------------------
def selection_changed(self, context):

    global Selected_Collection
    Selected_Collection=''

    prop,ui_list,itemlist = getprop()
    index = ui_list.active_index

    get_collection(itemlist[index].name)
    bpy.context.view_layer.active_layer_collection =  Selected_Collection


#----------------------------------------------------------
def get_collection(name):
    vlayer = bpy.context.view_layer #カレントビューレイヤー
    for c in vlayer.layer_collection.children:
        get_collection_loop(c,name)


def get_collection_loop( c ,name ):
    global Selected_Collection
    if c.name == name:
        Selected_Collection = c
    else:
        for c in c.children:
            get_collection_loop(c,name)

#名前でコレクションを取得する
def get_collectuion_by_name(name):
    global Selected_Collection
    get_collection(name)
    return Selected_Collection


#----------------------------------------------------------


#アイテム-------------------------------------------------------
#ItemPropertyはリストのに登録される一つのアイテムを表している

#リストからアイテムを取得
def get_item(self):
    return self["name"]

#リストに選択を登録する
def set_item(self, value):
    self["name"] = value

def showhide(self, value):
    ob = utils.getActiveObj()
    for mod in ob.modifiers :
            if mod.name == self["name"]:
                mod.show_viewport = self["bool_val"]


def clear():
    ui_list = bpy.context.window_manager.cyacollectioneditor_list
    itemlist = ui_list.itemlist
    itemlist.clear()


#---------------------------------------------------------------------------------------
def reload():
    ui_list = bpy.context.window_manager.cyacollectioneditor_list
    itemlist = ui_list.itemlist

    clear()
    # ob =utils.getActiveObj()

    for c in bpy.data.collections:
        print(c.name)
        item = itemlist.add()
        item.name = c.name


#オブジェクトモードかエディットモードかを
def add():
    ui_list = bpy.context.window_manager.cyacollectioneditor_list
    itemlist = ui_list.itemlist
    global Checked
    clear()
    # ob =utils.getActiveObj()

    for c in bpy.data.collections:
        if bpy.context.scene.user_of_id(c):#カレントシーンに存在するかどうか調べる
            print(c.name)
            item = itemlist.add()
            item.name = c.name

            if c.name in Checked:
                item.bool_val = True

#---------------------------------------------------------------------------------------

Checked=[]

def rename_add_sequential_number():
    props,ui_list,itemlist = getprop()
    name = props.rename_string

    global Checked
    Checked.clear()

    for i,node in enumerate(itemlist):
        if node.bool_val == True:
            col = bpy.data.collections[node.name]
            new = '%s_%02d' % (name , i+1 )
            col.name = new
            Checked.append(new)

    clear()
    add()


def rename_add_word( mode ):
    props,ui_list,itemlist = getprop()

    global Checked
    Checked.clear()

    if mode == 'suffix':
        word = props.rename_string
    elif mode == 'prefix':
        word = props.rename_string
    elif mode == 'suffix_list':
        word = props.word
    elif mode == 'prefix_list':
        word = props.word

    if(props.prefix_underbar):
        s='%s_%s'
    else:
        s='%s%s'

    for node in itemlist:
        if node.bool_val == True:
            col = bpy.data.collections[node.name]

            if mode == 'suffix' or mode == 'suffix_list':
                col.name = s % ( col.name , word )

            elif mode == 'prefix' or mode == 'prefix_list':
                col.name = s % ( word , col.name )

            Checked.append(col.name)

    clear()
    add()



def rename_replace():
    props,ui_list,itemlist = getprop()
    word = props.rename_string
    replace_word = props.replace_string

    global Checked
    Checked.clear()

    result = []
    for node in itemlist:
        if node.bool_val == True:
            col = bpy.data.collections[node.name]
            new = col.name.replace( word , replace_word )
            col.name = new
            Checked.append(new)

    clear()
    add()

#---------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------





def get_suffix():
    props = bpy.context.scene.cyaobjectlist_props
    suffix = props.suffix
    if suffix == 'none':
        suffix = ''
    else:
        suffix = '_' + suffix

    return suffix

def update_rename( result ):
    ui_list = bpy.context.window_manager.cyaobjectlist_list
    itemlist = ui_list.itemlist

    clear()
    for ob in result:
        item = itemlist.add()
        item.name = ob
        item.bool_val = True
        ui_list.active_index = len(itemlist) - 1


def select_all():
    ui_list = bpy.context.window_manager.cyaobjectlist_list
    itemlist = ui_list.itemlist

    if len(itemlist) == 0:
        return {"FINISHED"}

    for node in itemlist:
        utils.selectByName( node.name,True )
        #bpy.data.objects[node.name].select = True





def remove():
    ui_list = bpy.context.window_manager.cyaobjectlist_list
    itemlist = ui_list.itemlist

    if len(itemlist):
        itemlist.remove(ui_list.active_index)
        if len(itemlist)-1 < ui_list.active_index:
            ui_list.active_index = len(itemlist)-1
            if ui_list.active_index < 0:
                ui_list.active_index = 0


def remove_not_exist():
    ui_list = bpy.context.window_manager.cyaobjectlist_list
    itemlist = ui_list.itemlist
    index = ui_list.active_index

    if len(itemlist) == 0:
        return

    result = []
    for node in itemlist:
        if node.name in bpy.data.objects:
            print(node.name)
            result.append(node.name)

    itemlist.clear()

    for nodename in result:
        item = itemlist.add()
        item.name = nodename
        index = len(itemlist)-1


def move(dir):
    ui_list = bpy.context.window_manager.cyaobjectlist_list
    itemlist = ui_list.itemlist
    index = ui_list.active_index

    if len(itemlist) < 2:
        return

    if dir == 'UP':
        v = index -1
    elif dir == 'DOWN':
        v = index + 1

    itemlist.move(index, v)
    ui_list.active_index = v



#---------------------------------------------------------------------------------------
#ボーンクラスタのリネーム
#チェックを入れたもののみを対象とする
#---------------------------------------------------------------------------------------

#子供を取得
def bone_chain_loop(amt, bone, name, index ):
    for b in amt.data.edit_bones:
        if b.parent == bone:
            b.name = '%s_%02d%s' % (name , index , get_suffix() )

            bone_chain_loop(amt, b, name, index + 1 )

def rename_bonecluster():
    props = bpy.context.scene.cyaobjectlist_props
    name = props.rename_string

    ui_list = bpy.context.window_manager.cyaobjectlist_list
    itemlist = ui_list.itemlist

    amt = utils.getActiveObj()
    parentdic = {}

    rootarray = []
    count = 1
    utils.mode_e()

    for node in itemlist:
        if node.bool_val == True:
            b = amt.data.edit_bones[node.name]
            chainname = '%s_%02d' % (name , count )
            rootname = '%s_01%s' % (chainname  , get_suffix())

            b.name = rootname
            rootarray.append(b.name)
            bone_chain_loop(amt , b, chainname, 2 )
            count += 1
        else:
            rootarray.append(node.name)

    bpy.context.view_layer.update()

    clear()
    for name in rootarray:
        item = itemlist.add()
        item.name = name
        #ui_list.active_index = len(itemlist) - 1


def remove_check_item(op):
    ui_list = bpy.context.window_manager.cyaobjectlist_list
    itemlist = ui_list.itemlist

    #array = []
    indexarray = []
    for i,node in enumerate(itemlist):
        if op == 'checked':
            if node.bool_val == True:
            #array.append(node.name)
                indexarray.append(i)
        elif op == 'unchecked':
            if node.bool_val == False:
                indexarray.append(i)

    for index in reversed(indexarray):
        itemlist.remove(index)


#---------------------------------------------------------------------------------------
#チェックを入れたオブジェクトに関しての操作
#---------------------------------------------------------------------------------------
def check_item(op):
    props,ui_list,itemlist = getprop()
    # ui_list = bpy.context.window_manager.cyaobjectlist_list
    # itemlist = ui_list.itemlist

    if len(itemlist) == 0:
        return

    obset = set([ob.name for ob in bpy.context.selected_objects])
    if op == 'select':
        if utils.current_mode() == 'OBJECT':
            bpy.ops.object.select_all(action='DESELECT')
        if utils.current_mode() == 'EDIT':
            bpy.ops.armature.select_all(action='DESELECT')



    if(op == 0 or op == 1):
        for node in itemlist:
            if op == 0:
                if node.bool_val == True:
                    print(node.name)
                    collection_hide(node.name,False)

            elif op == 1:
                if node.bool_val == True:
                    collection_hide(node.name,True)
    else:
        col = utils.collection.get_active()
        if op == 2:
            collection_hide(col.name,False)
        if op == 3:
            collection_hide(col.name,True)

        get_collection(col.name)
        bpy.context.view_layer.active_layer_collection =  Selected_Collection

#チェックを入れたものの並びを反転する。
#インデックスを保持したままはめんどいので、ソートしたらリストの末尾に追加
#def invert():
    # ui_list = bpy.context.window_manager.cyaobjectlist_list
    # itemlist = ui_list.itemlist

        # elif op == 'invert':
        #     array = []
        #     indexarray = []
        #     for i,node in enumerate(itemlist):
        #         if node.bool_val == True:
        #             array.append(node.name)
        #             indexarray.append(i)

        #     for index in reversed(indexarray):
        #         itemlist.remove(index)

        #     for bone in reversed(array):
        #         item = itemlist.add()
        #         item.name = bone
        #         item.bool_val = True
        #         ui_list.active_index = len(itemlist) - 1






#----------------------------------------------------------df
#---------------------------------------------------------------------------------------
#選択オブジェクトのコレクションをハイド
#---------------------------------------------------------------------------------------
def collection_hide(name,state):
    #selected = utils.selected()
    layer = bpy.context.window.view_layer.layer_collection

    show_collection_by_name(layer ,name , state)

#---------------------------------------------------------------------------------------
#ビューレイヤーを名前で表示状態切替
#---------------------------------------------------------------------------------------
def show_collection_by_name(layer ,name , state):
    #props = bpy.context.scene.cyatools_oa
    children = layer.children

    if children != None:
        for ly in children:
            if name == ly.name:
                ly.hide_viewport = state

            show_collection_by_name(ly , name , state)