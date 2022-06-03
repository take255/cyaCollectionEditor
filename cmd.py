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

    clear()
    # ob =utils.getActiveObj()

    for c in bpy.data.collections:
        print(c.name)
        item = itemlist.add()
        item.name = c.name
#---------------------------------------------------------------------------------------

def rename_add_sequential_number():
    props,ui_list,itemlist = getprop()
    name = props.rename_string

    for i,node in enumerate(itemlist):
        if node.bool_val == True:
            col = bpy.data.collections[node.name]
            new = '%s_%02d' % (name , i+1 )
            col.name = new

    clear()
    add()



def rename_add_word( mode ):
    props,ui_list,itemlist = getprop()

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

    clear()
    add()



def rename_replace():
    props,ui_list,itemlist = getprop()

    word = props.rename_string
    replace_word = props.replace_string

    result = []
    for node in itemlist:
        if node.bool_val == True:
            col = bpy.data.collections[node.name]
            new = col.name.replace( word , replace_word )
            col.name = new

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
    ui_list = bpy.context.window_manager.cyaobjectlist_list
    itemlist = ui_list.itemlist

    if len(itemlist) == 0:
        return

    obset = set([ob.name for ob in bpy.context.selected_objects])
    if op == 'select':
        if utils.current_mode() == 'OBJECT':
            bpy.ops.object.select_all(action='DESELECT')
        if utils.current_mode() == 'EDIT':
            bpy.ops.armature.select_all(action='DESELECT')

    for node in itemlist:
        if op == 'selected':
            if utils.current_mode() == 'OBJECT':
                if node.name in obset:
                    node.bool_val = True
                else:
                    node.bool_val = False

            if utils.current_mode() == 'EDIT':
                obset = set([ob.name for ob in bpy.context.selected_bones])
                if node.name in obset:
                    node.bool_val = True
                else:
                    node.bool_val = False

            if utils.current_mode() == 'POSE':
                obset = set([ob.name for ob in bpy.context.selected_pose_bones])
                if node.name in obset:
                    if node.name in obset:
                        node.bool_val = True
                    else:
                        node.bool_val = False

        elif op == 'select':
            if node.bool_val == True:
                #オブジェクトモードなら
                if utils.current_mode() == 'OBJECT':
                    utils.selectByName(node.name,True)

                if utils.current_mode() == 'EDIT':
                    utils.bone.selectByName(node.name,True)

                if utils.current_mode() == 'POSE':
                    utils.bone.selectByName(node.name,True)


        elif op == 'show':
            if node.bool_val == True:
                utils.showhide(node,False)

        elif op == 'hide':
            if node.bool_val == True:
                utils.showhide(node,True)


#チェックを入れたものの並びを反転する。
#インデックスを保持したままはめんどいので、ソートしたらリストの末尾に追加
#def invert():
    # ui_list = bpy.context.window_manager.cyaobjectlist_list
    # itemlist = ui_list.itemlist
        elif op == 'invert':
            array = []
            indexarray = []
            for i,node in enumerate(itemlist):
                if node.bool_val == True:
                    array.append(node.name)
                    indexarray.append(i)

            for index in reversed(indexarray):
                itemlist.remove(index)

            for bone in reversed(array):
                item = itemlist.add()
                item.name = bone
                item.bool_val = True
                ui_list.active_index = len(itemlist) - 1


#---------------------------------------------------------------------------------------
#ボーンからクロスメッシュを生成
#揺れジョイント用
#---------------------------------------------------------------------------------------
def bone_clothmesh_loop( bone , chain ,vtxarray ,bonenamearray):
    amt = bpy.context.active_object
    for b in amt.data.edit_bones:
        if b.parent == bone:
            chain.append(b.name)
            bonenamearray.append(b.name)
            vtxarray.append(b.tail)
            bone_clothmesh_loop(b,chain ,vtxarray,bonenamearray)


#ジョイントのクラスタからメッシュを作成
#
def create_mesh_from_bone():
    props = bpy.context.scene.cyaobjectlist_props
    ui_list = bpy.context.window_manager.cyaobjectlist_list
    itemlist = ui_list.itemlist

    amt = bpy.context.object
    #selected = bpy.context.selected_bones
    num_col = 0
    num_row = len(itemlist)


    #頂点座標の配列生成
    #最初のボーンのheadだけの座標を入れれば、残りはtailの座標だけ入れていけばOK
    vtxarray = []

    bonenamearray = []
    chainarray = []

    utils.mode_e()
    for node in itemlist:
        bone = amt.data.edit_bones[node.name]
        chain = [bone.name]
        bonenamearray.append(bone.name)
        vtxarray += [bone.head , bone.tail ]
        bone_clothmesh_loop( bone , chain ,vtxarray ,bonenamearray)
        num_col = len(chain)
        chainarray.append(chain)

    polyarray = []
    ic = num_col + 1 #コラムの増分

    #ポリゴンのインデックス生成
    #円筒状にしたくない場合はrowを１つ減らす
    if props.cloth_open:
        row = num_row -1
    else:
        row = num_row

    for c in range(row):
        array = []
        for r in range(num_col):
            #シリンダ状にループさせたいので、最後のrowは一番目のrowを指定
            if c == num_row - 1:
                array = [
                    r + ic*c ,
                    r + 1 + ic*c ,
                    r + 1  ,
                    r
                    ]

            else:
                array = [
                    r + ic*c ,
                    r + 1 + ic*c ,
                    r + 1 + ic*(c + 1) ,
                    r + ic*(c + 1)
                    ]

            polyarray.append(array)

    #メッシュの生成
    mesh_data = bpy.data.meshes.new("cube_mesh_data")
    mesh_data.from_pydata(vtxarray, [], polyarray)
    mesh_data.update()


    obj = bpy.data.objects.new('test', mesh_data)

    scene = bpy.context.scene
    utils.sceneLink(obj)
    utils.select(obj,True)


    #IKターゲットの頂点グループ作成
    #ウェイト値の設定
    for j,chain in enumerate(chainarray):
        for i,bone in enumerate(chain):
            obj.vertex_groups.new(name = bone)
            index = 1 + i + j * (num_col+1)

            vg = obj.vertex_groups[bone]
            vg.add( [index], 1.0, 'REPLACE' )


    #IKのセットアップ
    utils.mode_o()
    utils.act(amt)
    utils.mode_p()


    for j,chain in enumerate(chainarray):
        for i,bone in enumerate(chain):

            jnt = amt.pose.bones[bone]
            c = jnt.constraints.new('IK')
            c.target = obj
            c.subtarget = bone
            c.chain_count = 1


    #クロスの設定
    #ピンの頂点グループを設定する
    pin = 'pin'
    obj.vertex_groups.new(name = pin)
    for c in range(num_row):
        index =  c * ( num_col + 1 )
        vg = obj.vertex_groups[pin]
        vg.add( [index], 1.0, 'REPLACE' )


    #bpy.ops.object.modifier_add(type='CLOTH')
    mod = obj.modifiers.new("cloth", 'CLOTH')
    mod.settings.vertex_group_mass = "pin"


def parent_chain():
    props = bpy.context.scene.cyaobjectlist_props

    ui_list = bpy.context.window_manager.cyaobjectlist_list
    itemlist = ui_list.itemlist

    amt = utils.getActiveObj()


    num = props.chain_step

    if num == 0:
        num = len(itemlist)
        step = 1
    else:
        #num = props.chain_step
        step = int(len(itemlist) / num)

    print('step>>',step)
    utils.mode_e()
    for s in range(step):

        for i in range(num-1):
            index0 = s * num + i
            index1 = s * num + i + 1

            bone = amt.data.edit_bones[itemlist[ index1 ].name]
            child = amt.data.edit_bones[itemlist[ index0 ].name]
            bone.tail = child.head


            bone = amt.data.edit_bones[itemlist[ index0 ].name]
            parent = amt.data.edit_bones[itemlist[ index1 ].name]
            bone.parent = parent
            bone.use_connect = True

        #Modify bone tail position.
        #for i in range(num-1):

