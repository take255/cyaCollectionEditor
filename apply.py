#from utils import selected
import bpy
import math
from mathutils import Matrix

from bpy.types import ( PropertyGroup , Panel)
from bpy.props import(
    PointerProperty,
    IntProperty,
    BoolProperty,
    StringProperty,
    CollectionProperty
    )

import imp

from . import utils
from . import locator
from . import cmd_

imp.reload(utils)
imp.reload(locator)
imp.reload(cmd_)

ApplyCollectionMode = False #apply_collectionで apply_collection_instanceを利用するためのフラグ
Collections = set()
#Collections_no_children = set() #子供コレクションを持っていないコレクション

class PublishedData:
    obj = None
    colname = ''
    mirror = False
    def __init__(self ,  obj , colname , mirror):
        self.obj = obj
        self.colname = colname
        self.mirror = mirror


def target_locator():
    props = bpy.context.scene.cyatools_oa
    scn = props.target_scene_name

    if bpy.data.scenes.get(scn) is None:
        print(u'Not found Scene')
        return False
    return scn


def doMerge():
    props = bpy.context.scene.cyatools_oa
    return props.merge_apply

def doMergeByMaterial():
    props = bpy.context.scene.cyatools_oa
    return props.merge_by_material

def doKeepHair():
    props = bpy.context.scene.cyatools_oa
    return props.keephair_apply

def doKeepArmature():
    props = bpy.context.scene.cyatools_oa
    return props.keeparmature_apply

def target_scene():
    props = bpy.context.scene.cyatools_oa
    return props.target_scene_name

def keepTransform():
    props = bpy.context.scene.cyatools_oa
    return props.keep_transform

#---------------------------------------------------------------------------------------
#コレクションのソート
#---------------------------------------------------------------------------------------
def collection_sort():
    children = []
    root = utils.collection.root()
    for c in root.children:
        children.append([c.name,c])

    children.sort()

    for c in children:
        root.children.unlink(c[1])

    for c in children:
        root.children.link(c[1])

#---------------------------------------------------------------------------------------
#コレクションに含まれているコレクションを取得
#コレクションの子供コレクションを再帰的に調べて全部取得する
#---------------------------------------------------------------------------------------
def get_obj_from_collection(x):
    Collections.add(x.name)
    for col in x.children.keys():
        get_obj_from_collection(x.children[col])


#---------------------------------------------------------------------------------------
#シーン内にあるコレクションを調べてコレクションやオブジェクトを所有していないものを削除
#何も含まれていないものを検索
#---------------------------------------------------------------------------------------
def remove_empty_collection():
    noEmpty = False
    for c in bpy.data.collections:
        if len(c.children) == 0  and len(c.objects) == 0:
            bpy.data.collections.remove(c)
            noEmpty = True

    if noEmpty:
        remove_empty_collection()


#---------------------------------------------------------------------------------------
#ロケータに親子付けする
#ロケータを作成してペアレント。ロケータがすでに存在していれば作成しない
#---------------------------------------------------------------------------------------
def parent_to_empty(current_scene_name , result):

    new_name = current_scene_name + '_parent'

    if bpy.data.objects.get(new_name) is not None:
        empty = utils.objectByName(new_name)

    else:
        bpy.ops.object.empty_add(type='PLAIN_AXES')
        empty = utils.getActiveObj()
        empty.name = new_name
        empty.matrix_world = Matrix()

    for obj in result:
        obj.parent = empty


#---------------------------------------------------------------------------------------
#パブリッシュ時にコレクションにまとめる
#orgのモデルがコレクションに属していれば、そのコレクションも複製
#コレクションが存在していて、かつ出力先にそのコレクションがない場合はエラーになる。その対処をする必要あり
#モデルがマスターにある場合の処理が必要
#create_collectionフラグ　新しくコレクションを作るかどうか。作らないならシーンのマスターコレクションにする
#---------------------------------------------------------------------------------------
def put_into_collection(current_scene_name , result ,scn):
    props = bpy.context.scene.cyatools_oa
    new_name = current_scene_name + '_collection'

    if not props.create_collection:
        col = scn.collection
        objects = [ob.name for ob in col.objects]

        for dat in result:
            if not dat.obj.name in objects:
            #if not dat.obj in col.objects:
                col.objects.link(dat.obj)
        return

    utils.collection.create(new_name)

    for dat in result:
        #所属していたコレクションがマスターでないなら
        # 'A_' + コレクション名  というコレクションに移動

        if dat.colname != 'Master Collection':
            new_name =  'A_' + dat.colname

            if new_name not in col.children.keys():
                col2 = bpy.data.collections.new(new_name)
                col.children.link(col2)

            col2 = col.children[new_name]
            col2.objects.link(dat.obj)
        else:
            col.objects.link(dat.obj)


#---------------------------------------------------------------------------------------
# This function allow you to put together objects into master collection of other scene.
#---------------------------------------------------------------------------------------
def put_into_mastercollection( result ,scn):
    col = scn.collection
    objects = [ob.name for ob in col.objects]

    for dat in result:
        for col0 in dat.obj.users_collection:
            col0.objects.unlink(dat.obj)

        col.objects.link(dat.obj)

        # if not dat.obj.name in objects:
        #     col.objects.link(dat.obj)
            #bpy.data.collections[dat.colname].objects.unlink(dat.obj)




#---------------------------------------------------------------------------------------
#髪の毛のコンバート
# #複数のヘアパーティクルがあることを想定
#---------------------------------------------------------------------------------------
def convert_hair(hairarray, new_name , ob):
    props = bpy.context.scene.cyatools_oa
    new_obj_array = []

    for num,hairname in enumerate(hairarray):
        utils.activeObj(ob)
        utils.select(ob,True)
        #コンバートするとメッシュオブジェクトが作られてそれがアクティブな状態になっている
        bpy.ops.object.modifier_convert(modifier = hairname)

        bpy.ops.object.convert(target='CURVE')
        new_obj = bpy.context.active_object

        new_obj_array.append(new_obj)

        #マスターコレクションを選択した状態で実行するとここでエラーがでる。不便そうなら解決策を考える
        bpy.ops.object.move_to_collection(collection_index = 0)
        new_obj.name = '%s_%02d' % (new_name,num)

        #カーブのサークルを作成してベベルに使用する
        #サークルカーブは終わったら削除
        #カーブにUVを設定することであとの調整を容易にする
        bpy.ops.curve.primitive_bezier_circle_add()
        circleobj = bpy.context.active_object
        circleobj.scale = (0.01,0.01,0.01)
        circleobj.data.resolution_u = 1 #<<<<<元は６。あとで数値入力できるように調整

        bpy.ops.object.move_to_collection(collection_index = 0)

        #テーパー用オブジェクト
        bpy.ops.curve.primitive_bezier_curve_add()
        taperobj = bpy.context.active_object
        taperobj.data.resolution_u = 6 #<<<<<元は６。あとで数値入力できるように調整

        bpy.ops.object.move_to_collection(collection_index = 0)

        new_obj.data.bevel_object = circleobj
        new_obj.data.taper_object = taperobj
        #new_obj.data.use_uv_as_generated = True
        new_obj.data.resolution_u = 1


        utils.select(new_obj,True)
        utils.activeObj(new_obj)

        #髪の毛をメッシュ化しない場合はベベルとテーパーカーブをFixScnに送る
        if not props.keephair_apply:
            utils.select(new_obj,False)
            utils.select(circleobj,True)
            utils.select(taperobj,True)
            utils.activeObj(circleobj)

            bpy.ops.object.delete()

        else:
           new_obj_array.append(circleobj)
           new_obj_array.append(taperobj)

    return new_obj_array


#---------------------------------------------------------------------------------------
#apply modelの第一段階
#パーティクルをカーブ化する
#ヘアーパーティクルの場合
#パーティクル削除にチェックがあったら髪の毛として処理しない
#複数のパーティクルがある場合に対応する必要あり
#---------------------------------------------------------------------------------------
def apply_model_sortout(ob , new_name , isMirror ):

    props = bpy.context.scene.cyatools_oa
    objs = bpy.data.objects
    col_name = ob.users_collection[0].name #現在所属しているコレクションを保持しておく

    result = None
    isHair = False

    utils.activeObj(ob)
    utils.select(ob,False)

    #既にモデルが存在していたら削除する
    #インスタンス実体化のときは無効
    if doDelSame:
        if bpy.data.objects.get(new_name) is not None:
            objs.remove(objs[new_name], do_unlink = True)

    hairarray = []
    for mod in ob.modifiers:
        if mod.type == 'PARTICLE_SYSTEM':
            if not props.deleteparticle_apply:#髪の毛として処理しない
                hairarray.append(mod.name)
                isHair = True

    #髪の毛でなければオブジェクトをコピーする。
    #髪の毛ならパーティクルをコンバートする
    if isHair:
        new_obj_array = convert_hair(hairarray, new_name , ob)
        for new_obj in new_obj_array:
            result = PublishedData(new_obj , col_name ,isMirror)

    #髪の毛でない場合
    else:
        new_obj = ob.copy()
        new_obj.data = ob.data.copy()
        new_obj.animation_data_clear()

        utils.sceneLink(new_obj)
        new_obj.name = new_name

        utils.select(new_obj,True)
        #utils.activeObj(new_obj)
        utils.act(new_obj)

        if len( [ x for x in new_obj.scale if x < 0 ] ) > 0:
            print(new_obj.name)
            utils.mode_e()
            bpy.ops.mesh.select_all(action='DESELECT')#全選択解除してからの
            bpy.ops.mesh.select_all(action='TOGGLE')#全選択

            bpy.ops.mesh.flip_normals()
            utils.mode_o()


        result = PublishedData( new_obj , col_name ,isMirror )

    return result

#---------------------------------------------------------------------------------------
#apply modelの第２段階
#モディファイヤの処理
#カーブならメッシュ化する。前のループで実行するとなぜかorgモデルまでメッシュ化してしまう。なのでここで実行する。
#髪の毛はここでメッシュ化される
#---------------------------------------------------------------------------------------
def apply_model_modifier(dat):

    props = bpy.context.scene.cyacollectioneditor_oa

    utils.act(dat.obj)
    bpy.ops.object.parent_clear(type = 'CLEAR_KEEP_TRANSFORM')#親子付けを切る

    #print('---------------------------------------------')
    #print(dat.obj.name , dat.obj.type , not doKeepHair())
    if dat.obj.type == 'CURVE':
        if not doKeepHair():
            bpy.ops.object.convert(target = 'MESH')

    #モディファイヤ適用

    for mod in dat.obj.modifiers:
        if mod.show_viewport == False:#モディファイヤが非表示なら削除する
            bpy.context.object.modifiers.remove(mod)

    if props.blendshape_apply:
        bpy.ops.object.apply_all_modifier()
    else:
        for mod in dat.obj.modifiers:
            if (mod.type == 'ARMATURE') and doKeepArmature():#アーマチュアをキープする
                pass

            elif mod.show_viewport == False:#モディファイヤが非表示なら削除する
                bpy.context.object.modifiers.remove(mod)
            else:
                try:#モディファイヤのターゲットがない場合など、適用でエラーが出る場合は削除
                    bpy.ops.object.modifier_apply(modifier=mod.name)
                    #bpy.ops.object.apply_all_modifier()
                except:
                    bpy.context.object.modifiers.remove(mod)

    #ミラーパブリッシュモード(この前のループで処理しようとするとエラーが出るのでここで実行)
    if dat.mirror:
        bpy.ops.object.transform_apply( location = True , rotation=True , scale=True )
        mod = dat.obj.modifiers.new( 'mirror' , type = 'MIRROR' )
        bpy.ops.object.modifier_apply(modifier=mod.name)

    #スケールにマイナスが入っているならアプライする

#---------------------------------------------------------------------------------------
#オブジェクトを別のシーンに移動
#---------------------------------------------------------------------------------------
def move_object_to_other_scene(mode):
    props = bpy.context.scene.cyatools_oa
    target = props.target_scene_name

    current = bpy.context.window.scene.name

    result = []
    for ob in utils.selected():
        col = ob.users_collection[0]
        result.append(PublishedData(ob , col.name ,False))

        if mode:
            col.objects.unlink(ob)

    put_into_collection(current , result ,bpy.data.scenes[target])
    set_current()
    utils.sceneActive(target)


#---------------------------------------------------------------------------------------
#コレクションを別のシーンに移動
#---------------------------------------------------------------------------------------
def move_collection_to_other_scene(mode):

    props = bpy.context.scene.cyatools_oa
    target = props.target_scene_name

    current = bpy.context.window.scene.name
    collection = bpy.context.view_layer.active_layer_collection

    move_collection_by_name( collection.name , target , mode )

    utils.sceneActive(target)
    set_current()


def move_collection_by_name( name , target , mode ):
    c = bpy.data.collections[name]

    #現在のコレクションからアンリンク
    if mode:
        for col in utils.collection.get_parent(c):
            col.children.unlink(c)

    bpy.data.scenes[target].collection.children.link(c)



#---------------------------------------------------------------------------------------
#コレクションに所属しているオブジェクトをapply
#mode:0 選択されたもの　mode:1 チェック付き
#---------------------------------------------------------------------------------------
def apply_collection(mode):
    props = bpy.context.scene.cyacollectioneditor_oa

    #現在のフレームを変更
    bpy.context.scene.frame_set( props.apply_frame )


    print('---------------------------------------------------')
    global ApplyCollectionMode
    ApplyCollectionMode = True #コレクションインスタンスの実体化時に強制マージする


    result = []
    if mode == 0:
        apply_collection_main(utils.collection.get_active())

    #チェックされたコレクションの処理
    elif mode == 1:
        prop,ui_list,itemlist = cmd_.getprop()


        for node in itemlist:
            utils.deselectAll()
            if node.bool_val == True:
                col = cmd_.get_collectuion_by_name(node.name)
                ob = apply_collection_main( col )
                result.append(ob)

    for ob in result:
        utils.select(ob,True)

def apply_collection_main(collection):
    props = bpy.context.scene.cyatools_oa

    only_directly_below = props.only_directly_below
    current_scene = bpy.context.scene

    current_frame = bpy.context.scene.frame_current
    for scn in bpy.data.scenes:
        utils.scene.active(scn)
        bpy.context.scene.frame_set(current_frame)

    utils.scene.active(current_scene)


    result = []
    print('only_directly_below',only_directly_below)
    if only_directly_below:
        for col in collection.children:
            utils.deselectAll()
            Collections.clear()
            get_obj_from_collection( col )#Collections配列に取得
            new_obj = apply_collection_loop(col.name)

            result.append( PublishedData( new_obj , collection.name ,False ) )

    else:
        Collections.clear()
        print('----->>>>')
        get_obj_from_collection( collection )#Collections配列に取得
        new_obj = apply_collection_loop(collection.name)
        result.append( PublishedData( new_obj , collection.name ,False ) )

    ApplyCollectionMode = False

    utils.deselectAll()
    return new_obj


#def apply_collection_loop(name , fix_scene):
def apply_collection_loop(name ):
    current_scene_name = bpy.context.scene.name
    current = bpy.context.scene

    #props = bpy.context.scene.cyatools_oa
    props = bpy.context.scene.cyacollectioneditor_oa

    #only_directly_below = props.only_directly_below
    # suffix = props.add_suffix
    # if suffix == True:
    #     new_name = name + '_orgc'
    # else:
    #     new_name = name
    new_name = name

    #選択されたコレクションにリンクされたオブジェクトを取得
    #print(Collections)
    for ob in bpy.context.scene.objects:

        user_cols = set([x.name for x in ob.users_collection])
        cols = set(Collections)
        #print(ob.name , user_cols & cols)
        #if set(cols) in Collections:
        if len(user_cols & cols) > 0:
            #ob.hide_viewport = True
            utils.select(ob,True)


    result = []
    #apply対象はメッシュかカーブ。それ以外は除外する
    for ob in utils.selected():
        print(ob.type)
        if ob.type == 'MESH' or ob.type == 'CURVE':

            result.append( apply_model_sortout( ob , ob.name + '_tmp', False ) )
        else:
            print(ob.name)
            utils.act(ob)
            #apply_collection_instanceでは強制マージしておきたい
            act = apply_collection_instance()
            #print(act.name)
            transform_apply()
            col_name = ob.users_collection[0].name
            result.append( PublishedData( act , col_name , False ) )# <<　複製されているモデルなのでapply_model_sortoutは使わない

            #put_into_collection(current_scene_name , result ,bpy.data.scenes[col_name])
            utils.scene.activebyname(current_scene_name)

    #コレクションにまとめ,強制マージ
    #カレントシーンにいったんまとめる
    #put_into_collection(current_scene_name , result , utils.sceneActive(current_scene_name))
    put_into_mastercollection( result , current )

    for dat in result:
        apply_model_modifier(dat)
        #utils.sceneUnlink(dat.obj)

    utils.multiSelection([x.obj for x in result])

    bpy.ops.object.join()

    #同名のモデルがあれば、語尾に_oldをつける
    if new_name in [ob.name for ob in bpy.data.objects]:
        ob = bpy.data.objects[new_name]
        utils.scene.move_obj_scene(ob)
        ob.name = new_name + '_old'
        #utils.delete(ob)

    utils.scene.active(current)
    act = utils.getActiveObj()

    #プレフィックス削除
    if props.delete_prefix:
        buf = new_name.split('_')
        size = len(buf[0])+1
        new_name = new_name[size:]
        #new_name = new_name.replace(f'{buf[0]}_','')
        act.name = new_name
    else:
        act.name = new_name

    return act



#---------------------------------------------------------------------------------------
#コレクションインスタンスをapply
#---------------------------------------------------------------------------------------
Duplicated = []
doDelSame =True

def instance_substantial_loop( col , current , matrix):
    act = utils.getActiveObj()
    col_org = locator.instance_select_collection() #インスタンス元のコレクションのオブジェクトを選択する

    #コレクションにコレクションが含まれていれば、その中身を選択
    #選択されたコレクションにリンクされたオブジェクトを取得
    Collections.clear()
    get_obj_from_collection(col_org)

    for ob in bpy.context.scene.objects:
        if ob.users_collection[0].name in Collections:
            # print('new_obj>>>>2',ob.name)
            # print(ob.hide_viewport)
            # ob.hide_viewport = False
            ob.hide_set(False)
            utils.select(ob,True)


    obarray = []
    selected = utils.selected()

    for ob in selected:
        utils.scene.move_obj_scene(ob)#オブジェクトが他のシーンある場合はそこに移動する
        utils.act(ob)
        if ob.data == None:
            if ob.instance_type == 'COLLECTION':
                m = matrix @ ob.matrix_world
                #instance_substantial_loop(col , current , m )
                instance_substantial_loop(col , current ,m)
        else:
            dat = apply_model_sortout( ob , ob.name + '_applied', False)#sortout内で複製
            Duplicated.append( dat )

            obj = dat.obj
            obj.hide_viewport = False
            #utils.collection.move_obj( obj , col )

            utils.act(obj)
            #ブーリアンモディファイヤはマトリックスをかける前に適用する必要がある
            for mod in obj.modifiers:
                if (mod.type == 'ARMATURE') and doKeepArmature():#アーマチュアをキープする
                    pass

                elif mod.show_viewport == False:#モディファイヤが非表示なら削除する
                    bpy.context.object.modifiers.remove(mod)
                else:
                    try:#モディファイヤのターゲットがない場合など、適用でエラーが出る場合は削除
                        bpy.ops.object.modifier_apply(modifier=mod.name)
                    except:
                        bpy.context.object.modifiers.remove(mod)

            obj.matrix_world =  matrix @ obj.matrix_world

        act = utils.getActiveObj()
        #act.hide_viewport = False
    #bpy.context.view_layer.update()
    utils.deselectAll()
    scn = utils.sceneActive(current)


#---------------------------------------------------------------------------------------
#apply Collection Instance
#---------------------------------------------------------------------------------------
def apply_collection_instance():

    global doDelSame
    global ApplyCollectionMode

    doDelSame = False #同名モデル削除しない
    keeptransform = keepTransform()

    #強制マージがONならマージ。OFFならメニューの設定に準ずる
    if ApplyCollectionMode:
        domerge = True
    else:
        domerge = doMerge()


    domergebymaterial = doMergeByMaterial()
    fix_scene = target_scene()
    #シーンの切り替えがあるため、カレントシーンの設定をここで取得しておく。

    target_col = bpy.data.scenes[fix_scene].collection
    current = bpy.context.window.scene.name


    for ob in utils.selected():
        Duplicated.clear()
        utils.act(ob)
        #act = utils.getActiveObj()
        act = ob

        #If actname contain '_org' , delete '_org'.
        actname = act.name

        if actname.find('_org') != -1:
            actname = actname.replace('_org','')


        #トランスフォームは一度初期化。マトリックスは最後にかける
        #コンストレインでミラーしている場合は、姿勢を戻したときにコンストレインが不具合を起こす
        #コンストレインを切った状態のマトリックスを保持して対処

        matrix = Matrix(act.matrix_world) #複製したものに使うマトリックス

        #コンストレインをすべてオフにする
        for const in act.constraints:
            const.mute = True

        bpy.context.view_layer.update()#コンストレイン解除時のマトリックスを強制アップデート
        matrix_source = Matrix(act.matrix_world) #コピー元のモデルのためのマトリックス

        act.matrix_world = Matrix()


        if act.instance_type != 'COLLECTION':
            return


        #モデルを置くコレクションを指定
        col = utils.collection.create('98_substantial')
        # if not ApplyCollectionMode:
        #     col = utils.collection.create('01_substantial')
        # else:
        #     col = utils.collection.root()


        #このコレクションがカレントシーンにない場合はエラーになる
        #コレクションが無い場合はカレントにコピーしてくる
        if not utils.collection.exist(col):
            utils.collection.move_col(col)

        instance_substantial_loop( col , current ,Matrix())

        for dat in Duplicated:
            utils.scene.move_obj_scene(dat.obj)#オブジェクトが他のシーンある場合はそこに移動する
            apply_model_modifier(dat)
            utils.act(dat.obj)
            if not keeptransform:
                transform_apply()


        #姿勢を元に戻し、コンストレインを復帰させる
        #元のコンスト状態を保持しておらず、すべてONにする処理をしてるので、問題がおきるかも
        act.matrix_world = matrix_source
        for const in act.constraints:
            const.mute = False


        #コレクションにまとめ,強制マージ
        # apply_collectionで利用する場合はmoveしない
        if domerge:
            # print('dup>>',Duplicated)
            # for obj in [x.obj for x in Duplicated]:
            #     print('name>>>',obj.name)
            #     obj.hide_viewport = False

            utils.multiSelection([x.obj for x in Duplicated])
            bpy.ops.object.join()
            transform_apply()

            act = utils.getActiveObj()

            if not ApplyCollectionMode:
                utils.collection.move_obj( act , target_col )# Here, move to target scene.
            else:
                utils.collection.move_obj_to_root(act)

            act.matrix_world =  matrix @ act.matrix_world

            utils.scene.move_obj_scene(act)#In the case not exist obj in current scene, move to fit scene.
            utils.act(act)
            transform_apply()#マージされたあとのモデルをアプライ
            act.name = actname

        #マテリアルでモデルを仕分けする
        elif domergebymaterial:
            dic = {}
            for ob in [x.obj for x in Duplicated]:
                materials = ob.data.materials
                print(materials)
                if len(materials) != 0:
                    mat = materials[0].name
                    if mat in dic.keys():
                        dic[mat].append(ob)
                    else:
                        dic[mat] = [ob]


            for v in dic.values():
                utils.deselectAll()
                utils.multiSelection(v)

                bpy.ops.object.join()
                transform_apply()
                act = utils.getActiveObj()

                if not ApplyCollectionMode:
                    utils.collection.move_obj( act , target_col )

                act.matrix_world =  matrix @ act.matrix_world

        #マージはしない
        else:
            for ob in [x.obj for x in Duplicated]:

                if not ApplyCollectionMode:
                    utils.collection.move_obj( ob , target_col )

                ob.matrix_world =  matrix @ ob.matrix_world

        utils.sceneActive(current)


    if not ApplyCollectionMode:
        utils.sceneActive(fix_scene)

    doDelSame = True
    return utils.getActiveObj()




#---------------------------------------------------------------------------------------
#apply Collection Instance
#---------------------------------------------------------------------------------------
def apply_collection_instance_():

    global doDelSame
    global ApplyCollectionMode

    doDelSame = False #同名モデル削除しない
    keeptransform = keepTransform()

    #強制マージがONならマージ。OFFならメニューの設定に準ずる
    if ApplyCollectionMode:
        domerge = True
    else:
        domerge = doMerge()


    domergebymaterial = doMergeByMaterial()
    fix_scene = target_scene()
    #シーンの切り替えがあるため、カレントシーンの設定をここで取得しておく。

    target_col = bpy.data.scenes[fix_scene].collection

    Duplicated.clear()
    current = bpy.context.window.scene.name


    act = utils.getActiveObj()

    #If actname contain '_org' , delete '_org'.
    actname = act.name

    if actname.find('_org') != -1:
        actname = actname.replace('_org','')


    #トランスフォームは一度初期化。マトリックスは最後にかける
    #コンストレインでミラーしている場合は、姿勢を戻したときにコンストレインが不具合を起こす
    #コンストレインを切った状態のマトリックスを保持して対処

    matrix = Matrix(act.matrix_world) #複製したものに使うマトリックス

    #コンストレインをすべてオフにする
    for const in act.constraints:
        const.mute = True

    bpy.context.view_layer.update()#コンストレイン解除時のマトリックスを強制アップデート
    matrix_source = Matrix(act.matrix_world) #コピー元のモデルのためのマトリックス

    act.matrix_world = Matrix()


    if act.instance_type != 'COLLECTION':
        return


    #モデルを置くコレクションを指定
    col = utils.collection.create('98_substantial')
    # if not ApplyCollectionMode:
    #     col = utils.collection.create('01_substantial')
    # else:
    #     col = utils.collection.root()


    #このコレクションがカレントシーンにない場合はエラーになる
    #コレクションが無い場合はカレントにコピーしてくる
    if not utils.collection.exist(col):
        utils.collection.move_col(col)

    instance_substantial_loop( col , current ,Matrix())

    for dat in Duplicated:
        utils.scene.move_obj_scene(dat.obj)#オブジェクトが他のシーンある場合はそこに移動する
        apply_model_modifier(dat)
        utils.act(dat.obj)
        if not keeptransform:
            transform_apply()


    #姿勢を元に戻し、コンストレインを復帰させる
    #元のコンスト状態を保持しておらず、すべてONにする処理をしてるので、問題がおきるかも
    act.matrix_world = matrix_source
    for const in act.constraints:
        const.mute = False


    #コレクションにまとめ,強制マージ
    # apply_collectionで利用する場合はmoveしない
    if domerge:
        # print('dup>>',Duplicated)
        # for obj in [x.obj for x in Duplicated]:
        #     print('name>>>',obj.name)
        #     obj.hide_viewport = False

        utils.multiSelection([x.obj for x in Duplicated])
        bpy.ops.object.join()
        transform_apply()

        act = utils.getActiveObj()

        if not ApplyCollectionMode:
            utils.collection.move_obj( act , target_col )# Here, move to target scene.
        else:
            utils.collection.move_obj_to_root(act)

        act.matrix_world =  matrix @ act.matrix_world

        utils.scene.move_obj_scene(act)#In the case not exist obj in current scene, move to fit scene.
        utils.act(act)
        act.name = actname

    #マテリアルでモデルを仕分けする
    elif domergebymaterial:
        dic = {}
        for ob in [x.obj for x in Duplicated]:
            materials = ob.data.materials
            print(materials)
            if len(materials) != 0:
                mat = materials[0].name
                if mat in dic.keys():
                    dic[mat].append(ob)
                else:
                    dic[mat] = [ob]


        for v in dic.values():
            utils.deselectAll()
            utils.multiSelection(v)

            bpy.ops.object.join()
            transform_apply()
            act = utils.getActiveObj()

            if not ApplyCollectionMode:
                utils.collection.move_obj( act , target_col )

            act.matrix_world =  matrix @ act.matrix_world

    #マージはしない
    else:
        for ob in [x.obj for x in Duplicated]:

            if not ApplyCollectionMode:
                utils.collection.move_obj( ob , target_col )

            ob.matrix_world =  matrix @ ob.matrix_world

    if not ApplyCollectionMode:
        utils.sceneActive(fix_scene)


    doDelSame = True
    return utils.getActiveObj()

#---------------------------------------------------------------------------------------
#トランスフォームをアプライする
#スケールの正負判定　スケールに一つでも負の値が入っていたら法線をフリップする
#---------------------------------------------------------------------------------------
def transform_apply():
    act = utils.getActiveObj()

    if len( [ x for x in act.scale if x < 0 ] ) > 0:
        utils.mode_e()
        bpy.ops.mesh.select_all(action='DESELECT')#全選択解除してからの
        bpy.ops.mesh.select_all(action='TOGGLE')#全選択

        bpy.ops.mesh.flip_normals()
        utils.mode_o()
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True, properties=True)



#---------------------------------------------------------------------------------------
#モデル名に_orgがついたものをapply対象とする
#---------------------------------------------------------------------------------------
def model_org():
    fix_scn = target_scene()
    domerge = doMerge()
    if not fix_scn:
        return
    current_scene_name = bpy.context.scene.name

    result = []
    for ob in utils.selected():
        isOrg = False
        isMirror = False

        name = ob.name
        #objの末尾に_orgがついていなければスルー
        if name[-3:] == 'org':
            new_name = name.replace('_org','')
            isOrg = True

        if name[-4:] == 'orgm':
            new_name = name.replace('_orgm','')
            isOrg = True
            isMirror = True

        if isOrg:
            result.append( apply_model_sortout(ob , new_name , isMirror) )

    utils.deselectAll()
    for dat in result:
        apply_model_modifier(dat)


    #シーンごとのコレクションにまとめるので下記は不要。
    # この行を有効にすると親のコレクションにも含まれてしまい2重に表示されてしまう。
    #bpy.ops.object.make_links_scene(scene = fix_scene)

    for dat in result:
        utils.sceneUnlink(dat.obj)

    scn = utils.sceneActive(fix_scn)
    put_into_collection(current_scene_name , result , scn)

    #マージする
    if domerge:
        utils.multiSelection([x.obj for x in result])
        bpy.ops.object.join()

    set_current()




#現在のシーンをシーンメニューにセット
def set_current():
    props = bpy.context.scene.cyatools_oa

    props.allscene.clear()
    props.target_allscene.clear()

    for scn in bpy.data.scenes:
        props.allscene.add().name = scn.name
        props.target_allscene.add().name = scn.name

    props.scene_name = bpy.context.scene.name

    # set_current_scene
    # scene.set_current