import bpy
from bpy.types import (PropertyGroup , UIList , Operator)
import imp

from .. import utils
imp.reload(utils)


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


#---------------------------------------------------------------------------------------
def reload():
    ui_list = bpy.context.window_manager.cyamodifierlist_list
    itemlist = ui_list.itemlist

    clear()
    ob =utils.getActiveObj()

    for mod in ob.modifiers:
        item = itemlist.add()
        item.name = mod.name
        item.bool_val = mod.show_viewport
        ui_list.active_index = len(itemlist) - 1

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

#---------------------------------------------------------------------------------------
#リストのモディファイヤを探しだし、リストでの順位とモディファイヤの順位を比較する
#その差を出してmove_upで順番を変更する
#---------------------------------------------------------------------------------------
# def move(type):
#     ui_list = bpy.context.window_manager.cyamodifierlist_list
#     itemlist = ui_list.itemlist
#     index = ui_list.active_index

#     if len(itemlist) < 2:
#         return

#     if type == 'UP':
#         v = index -1
#     elif type == 'DOWN':
#         v = index + 1
#     elif type == 'TOP':
#         v = 0
#     elif type == 'BOTTOM':
#         v = len(itemlist) - 1


#     itemlist.move(index, v)
#     ui_list.active_index = v

#     ob =utils.getActiveObj()

#     for order_list,listitem in enumerate(itemlist):
#         for order,mod in enumerate(ob.modifiers):

#             if mod.name == listitem.name:
#                 if (order_list < order):
#                     for i in range(order - order_list):
#                         bpy.ops.object.modifier_move_up(modifier = mod.name )




def select_all():
    ui_list = bpy.context.window_manager.cyaobjectlist_list
    itemlist = ui_list.itemlist

    if len(itemlist) == 0:
        return {"FINISHED"}

    for node in itemlist:
        utils.selectByName( node.name,True )
        #bpy.data.objects[node.name].select = True


#オブジェクトモードかエディットモードかを
def add():
    ui_list = bpy.context.window_manager.cyaobjectlist_list
    itemlist = ui_list.itemlist

    mode = utils.current_mode()
    if mode == 'OBJECT':
        for ob in utils.selected():
            item = itemlist.add()
            item.name = ob.name
            item.bool_val = True
            ui_list.active_index = len(itemlist) - 1

    elif mode == 'EDIT':
        for bone in utils.get_selected_bones():
            item = itemlist.add()
            item.name = bone.name
            item.bool_val = True
            ui_list.active_index = len(itemlist) - 1

    elif mode == 'POSE':
        for bone in utils.get_selected_bones():
            item = itemlist.add()
            item.name = bone.name
            item.bool_val = True
            ui_list.active_index = len(itemlist) - 1



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


def clear():
    ui_list = bpy.context.window_manager.cyaobjectlist_list
    itemlist = ui_list.itemlist
    itemlist.clear()

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



#---------------------------------------------------------------------------------------
#rename for UE4
#---------------------------------------------------------------------------------------
ARM = ('clavicle' , 'upperarm' , 'lowerarm' , 'hand')
LEG = ('thigh' , 'calf' , 'foot' , 'ball')
ARM_TWIST = ('upperarm_twist_01','lowerarm_twist_01')
LEG_TWIST = ('thigh_twist_01','calf_twist_01')
FINGER = ('thumb' , 'index' ,'middle' , 'ring' , 'pinky' )

def bonechain_ue4_finger_loop( bone , index , name ):
    props = bpy.context.scene.cyaobjectlist_props
    amt = bpy.context.active_object
    for b in amt.data.edit_bones:
        if b.parent == bone:
            b.name = '%s_%02d_%s' % ( name , index , props.setupik_lr )
            bonechain_ue4_finger_loop(b , index + 1 , name)

def bonechain_ue4(part):
    props = bpy.context.scene.cyaobjectlist_props
    # for b in amt.data.edit_bones:
    #     if b.parent == bone:
    #         chain.append(b.name)
    #         bonenamearray.append(b.name)
    #         vtxarray.append(b.tail)
    #         bone_chain_loop(b,chain ,vtxarray,bonenamearray)

    ui_list = bpy.context.window_manager.cyaobjectlist_list
    itemlist = ui_list.itemlist
    index = ui_list.active_index

    amt = bpy.context.active_object

    result = []
    utils.mode_e()
    if part == 'clavile_hand':
        rename_ue4_1(ARM,result)

    if part == 'thigh_toe':
        rename_ue4_1(LEG,result)

    elif part == 'arm_twist':
        rename_ue4_1(ARM_TWIST,result)

    elif part == 'leg_twist':
        rename_ue4_1(LEG_TWIST,result)

    elif part == 'pelvis_spine':
        l = [i.name for i in itemlist]
        pelvisname = l.pop(0)
        pelvis = amt.data.edit_bones[pelvisname]
        pelvis.name = 'pelvis'
        result.append( pelvis.name )

        for i , b in enumerate(l):
            bone = amt.data.edit_bones[b]
            bone.name = 'spine_%02d' % (i + 1)
            result.append(bone.name)

    elif part == 'neck_head':
        l = [i.name for i in itemlist]
        headname = l.pop()
        head = amt.data.edit_bones[headname]
        head.name = 'head'
        result.append( head.name )

        for i , b in enumerate(l):
            bone = amt.data.edit_bones[b]
            bone.name = 'neck_%02d' % (i + 1)
            result.append(bone.name)


    #pinky_01_l
    elif part == 'finger':
        for newname , b in zip( FINGER , itemlist ):
            bone = amt.data.edit_bones[b.name]
            bone.name = '%s_01_%s' % ( newname , props.setupik_lr )
            bonechain_ue4_finger_loop( bone , 2 , newname )


    #reload list
    clear()
    for ob in result:
        item = itemlist.add()
        item.name = ob
        ui_list.active_index = len(itemlist) - 1


def rename_ue4_1( namearray ,result):
    amt = bpy.context.active_object
    props = bpy.context.scene.cyaobjectlist_props
    ui_list = bpy.context.window_manager.cyaobjectlist_list
    itemlist = ui_list.itemlist

    for new , b in zip( namearray , itemlist ):
        bone = amt.data.edit_bones[b.name]
        bone.name = '%s_%s' % ( new , props.setupik_lr)
        result.append(bone.name)


#---------------------------------------------------------------------------------------
#Bone rename tool
#---------------------------------------------------------------------------------------

def rename_replace(mode):
    props = bpy.context.scene.cyaobjectlist_props

    ui_list = bpy.context.window_manager.cyaobjectlist_list
    itemlist = ui_list.itemlist

    amt = utils.getActiveObj()
    utils.mode_e()

    word = props.rename_string
    replace_word = props.replace_string

    result = []
    for node in itemlist:
        if node.bool_val == True:
            b = amt.data.edit_bones[node.name]

            if mode == 'replace':
                new = b.name.replace( word , replace_word )

            elif mode == 'l>r':
                new = b.name.replace( '_l' , '_r' )

            elif mode == 'r>l':
                new = b.name.replace( '_r' , '_l' )

            elif mode == 'del.number':
                new = b.name.split('.')[0]

            b.name = new
            result.append(b.name)

    update_rename(result)
    # clear()

    # for ob in result:
    #     item = itemlist.add()
    #     item.name = ob
    #     item.bool_val = True
    #     ui_list.active_index = len(itemlist) - 1


def rename_add_word( mode ):
    props = bpy.context.scene.cyaobjectlist_props

    ui_list = bpy.context.window_manager.cyaobjectlist_list
    itemlist = ui_list.itemlist

    amt = utils.getActiveObj()
    utils.mode_e()

    if mode == 'suffix':
        word = props.rename_string
    elif mode == 'prefix':
        word = props.rename_string
    elif mode == 'suffix_list':
        word = props.suffix

    #replace_word = props.replace_string

    if(props.prefix_underbar):
        s='%s_%s'
    else:
        s='%s%s'

    result = []
    for node in itemlist:
        if node.bool_val == True:
            b = amt.data.edit_bones[node.name]

            if mode == 'suffix' or mode == 'suffix_list':
                b.name = s % ( b.name , word )

            elif mode == 'prefix':
                b.name = s % ( word , b.name )

            result.append(b.name)

    clear()

    for ob in result:
        item = itemlist.add()
        item.name = ob
        ui_list.active_index = len(itemlist) - 1
        item.bool_val = True


def bonechain_finger_loop( bone , index , name ):
    props = bpy.context.scene.cyaobjectlist_props
    amt = bpy.context.active_object
    for b in amt.data.edit_bones:
        if b.parent == bone:
            b.name = '%s_%02d_%s' % ( name , index , props.setupik_lr )
            bonechain_finger_loop(b , index + 1 , name)


def rename_finger(mode):
    prefix = ['' , 'toe']
    props = bpy.context.scene.cyaobjectlist_props

    ui_list = bpy.context.window_manager.cyaobjectlist_list
    itemlist = ui_list.itemlist

    amt = utils.getActiveObj()
    parentdic = {}

    rootarray = []

    utils.mode_e()
    count = 0
    for node in itemlist:
        if node.bool_val == True:
            name = prefix[mode] + FINGER[ count ]
            b = amt.data.edit_bones[node.name]
            rootname = name + '_01_' + props.setupik_lr

            b.name = rootname
            rootarray.append(b.name)
            bonechain_finger_loop( b, 2, name )
            count += 1
        else:
            rootarray.append(node.name)

    bpy.context.view_layer.update()

    clear()

    for name in rootarray:
        item = itemlist.add()
        item.name = name
        item.bool_val = True


def rename_add_sequential_number():
    props = bpy.context.scene.cyaobjectlist_props
    ui_list = bpy.context.window_manager.cyaobjectlist_list
    itemlist = ui_list.itemlist
    name = props.rename_string

    # suffix = props.suffix
    # if suffix == 'none':
    #     suffix = ''
    # else:
    #     suffix = '_' + suffix

    amt = utils.getActiveObj()

    bonearray = []
    utils.mode_e()
    for i,node in enumerate(itemlist):
        if node.bool_val == True:
            b = amt.data.edit_bones[node.name]
            new = '%s_%02d%s' % (name , i+1 , get_suffix() )
            new = '%s_%02d' % (name , i+1 )
            b.name = new
            bonearray.append(new)

    clear()

    for n in bonearray:
        item = itemlist.add()
        item.name = n
        item.bool_val = True


