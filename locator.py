import bpy
import bmesh
import imp

from mathutils import ( Matrix , Vector )

from . import utils
imp.reload(utils)

#---------------------------------------------------------------------------------------
#モデルに位置にロケータを配置してコンストレインする。
#中間にロケータをかます。親のロケータの形状をsphereにする。
#モデルのトランスフォームは初期値にする
#ロケータを '09_ConstRoot'　に入れる
#コレクションをインスタンスに差し替える関数追加
#---------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------
#オブジェクトをコレクションに移動
#---------------------------------------------------------------------------------------
def move_collection( ob , col ):
    collections = ob.users_collection
    for c in collections:
         c.objects.unlink(ob)

    col.objects.link(ob)


#---------------------------------------------------------------------------------------
def create_locator_collection():
    scn = bpy.context.scene
    colname = '09_ConstRoot'
    #コレクションが存在していればそのまま使用、なければ新規作成
    if colname in scn.collection.children.keys():
        col = scn.collection.children[colname]

    else:
        col = bpy.data.collections.new(colname)
        scn.collection.children.link(col)
    return col



def tobone():
    selected = utils.selected()
    result = []

    #amt = [x for x in selected if x.type == 'ARMATURE']
    amt = utils.getActiveObj()
    bone  = utils.bone.get_active_bone()
    matrix = Matrix(bone.matrix)

    matrix.invert()
    location = Vector(bone.head)
    mat_loc = Matrix.Translation(Vector(bone.head))

    #アーマチュアをエディットモードのままにしておくと選択がおかしくなるのでいったん全選択解除
    bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

    #ロケータ生成
    bpy.ops.object.empty_add(type='PLAIN_AXES')
    empty = bpy.context.active_object

    c =empty.constraints.new('COPY_TRANSFORMS')
    c.target = amt
    c.subtarget = bone.name
    c.target_space ='WORLD'
    c.owner_space = 'WORLD'
    bpy.context.view_layer.update()

    for obj in selected:
        if obj.type != 'ARMATURE':
            obj.parent = empty
            bpy.context.view_layer.update()
            m = mat_loc @ matrix @ Matrix(obj.matrix_world)
            #m_rot = m.to_3x3()#位置をクリアする

            obj.matrix_world = m


def tobone_keep():
    selected = utils.selected()
    result = []

    amt = utils.getActiveObj()
    bone  = utils.bone.get_active_bone()
    matrix = Matrix(bone.matrix)

    matrix.invert()
    location = Vector(bone.head)
    mat_loc = Matrix.Translation(Vector(bone.head))

    mat_loc.invert()
    #アーマチュアをエディットモードのままにしておくと選択がおかしくなるのでいったん全選択解除
    bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

    #ロケータ生成
    bpy.ops.object.empty_add(type='PLAIN_AXES')
    empty = bpy.context.active_object

    c =empty.constraints.new('COPY_TRANSFORMS')
    c.target = amt
    c.subtarget = bone.name
    c.target_space ='WORLD'
    c.owner_space = 'WORLD'
    bpy.context.view_layer.update()

    for obj in selected:
        if obj.type != 'ARMATURE':
            obj.parent = empty
            bpy.context.view_layer.update()
            m = matrix @ Matrix(obj.matrix_world)

            obj.matrix_world = m




#---------------------------------------------------------------------------------------
def create_locator(name , matrix):

    col = create_locator_collection()

    #ロケータを作成
    bpy.ops.object.empty_add(type='PLAIN_AXES')
    empty = bpy.context.active_object
    empty.name =  name + '_constlocator'
    empty.matrix_world = matrix

    move_collection(empty , col)


    #親のロケータを作成
    bpy.ops.object.empty_add(type='SPHERE')
    empty_p = bpy.context.active_object
    empty_p.name = name + '_parent'
    empty_p.matrix_world = Matrix()

    move_collection(empty_p , col)

    constraint =empty_p.constraints.new('COPY_TRANSFORMS')
    constraint.target = empty
    constraint.target_space ='WORLD'
    constraint.owner_space = 'WORLD'

    return empty_p

#---------------------------------------------------------------------------------------
#replace : オブジェクトをロケータの子供にして扱いやすくする
#選択モデルをロケータに親子付けをしてコンストレイン。
#---------------------------------------------------------------------------------------
def replace():
    selected = utils.selected()

    for obj in selected:
        empty_p = create_locator(obj.name , obj.matrix_world)

        obj.matrix_world = Matrix()
        obj.parent = empty_p


#---------------------------------------------------------------------------------------
#エディットモードで選択したフェースのノーマルを基準にロケータを生成する
#法線方向が(0,0,1)の時は例外処理する必要あり。内積をとって判定。
#---------------------------------------------------------------------------------------
def replace_facenormal():

    obj = bpy.context.edit_object
    me = obj.data
    bm = bmesh.from_edit_mesh(me)

    upvector = Vector((0,0,1.0))
    upvector_x = Vector((-1.0,0,0))

    for f in bm.faces:
        if f.select:
            pos = f.calc_center_bounds()
            normal = f.normal
            xaxis = f.calc_tangent_edge()
            yaxis = xaxis.cross(normal)

            normal.normalize()
            xaxis.normalize()
            yaxis.normalize()

            x = [x for x in xaxis] +[0.0]
            y = [x for x in yaxis] +[0.0]
            z = [x for x in normal] +[0.0]
            p = [x for x in pos] +[0.0]

            m0 = Matrix([xaxis,yaxis,normal])
            m0.transpose()

            matrix = Matrix([x , y , z , p])
            matrix.transpose()


    utils.mode_o()

    empty_p = create_locator(obj.name , matrix)

    #親子付けする前に逆変換しておいて親子付け時の変形を打ち消す
    mat_loc = Matrix.Translation([-x for x in pos])
    obj.matrix_world = m0.inverted().to_4x4() @ mat_loc

    obj.parent = empty_p

#---------------------------------------------------------------------------------------
#選択したモデルをロケータでまとめる
#アクティブなモデルの名前を継承する
#---------------------------------------------------------------------------------------
def group():
    selected = utils.selected()
    act = utils.getActiveObj()
    locatorname = act.name + '_parent'

    bpy.ops.object.empty_add(type='PLAIN_AXES')
    empty = utils.getActiveObj()
    empty.name = locatorname
    empty.matrix_world = Matrix()

    for obj in selected:
        obj.parent = empty



#---------------------------------------------------------------------------------------
#コレクションをインスタンス化
#元モデルを原点にもってくる。選択したモデルをピボットとし、メンバーになっているコレクションを対象
#---------------------------------------------------------------------------------------
def instancer():
    col = bpy.context.scene.collection

    #選択したオブジェクトのコレクションを選択
    #回転matrixと位置vectorに分ける
    act = utils.getActiveObj()
    pos_act = Vector(act.location)
    m_rot = act.matrix_world.to_3x3()
    m_rot.invert()

    matrix = Matrix(act.matrix_world)
    col_selected = act.users_collection[0]


    #平行移動
    for ob in col_selected.objects:
        ob.location -= pos_act

    #回転
    for ob in col_selected.objects:
        pos = Vector(ob.location)
        pos_new = m_rot @ pos
        print (ob.name , ob.location , pos)
        m = m_rot @ ob.matrix_world.to_3x3()
        ob.matrix_world = m.to_4x4()
        ob.location = pos_new

    #インスタンス　空オブジェクトを作成
    instance = bpy.data.objects.new(col_selected.name , None)
    instance.instance_collection = col_selected
    instance.instance_type = 'COLLECTION'
    instance.matrix_world  = matrix

    col.objects.link(instance)

#---------------------------------------------------------------------------------------
#コレクション実体化のループ
#コレクションの中にコレクションがある場合、再帰的に実体化していく
#インスタンス元のモデルを選択して複製、コレクションに入れてインスタンスコレクションを差し替え
#選択物がインスタンスだったら dataを調べてNoneを返せばメッシュではない
#インスタンスを実体化したら、複製したインスタンスオブジェクトを削除する
#---------------------------------------------------------------------------------------

Duplicated = []

def instance_substantial_loop( col , current ):
    act = utils.getActiveObj()
    matrix = Matrix(act.matrix_world)
    col_org = instance_select_collection() #インスタンス元のコレクションのオブジェクトを選択する

    obarray = []
    selected = utils.selected()

    for ob in selected:
        utils.act(ob)
        if ob.data == None:
            if ob.instance_type == 'COLLECTION':
                instance_substantial_loop(col , current)
        else:
            bpy.ops.object.duplicate_move()
            act = utils.getActiveObj()
            col.objects.link(act)
            col_org.objects.unlink(act)
            Duplicated.append(act)
            # print(act.name)
            # for mod in act.modifiers:
            #     bpy.ops.object.modifier_apply( modifier = mod.name )

        act = utils.getActiveObj()
        #obarray.append(act.name)

    utils.deselectAll()

    scn = utils.sceneActive(current)

    # for ob in obarray:
    #     print(ob)
    #     utils.selectByName(ob,True)




    #act = utils.getActiveObj()
    transform_apply()
    try:
        act.matrix_world = matrix
    except:
        pass


#---------------------------------------------------------------------------------------
#インスタンスを実体化
#---------------------------------------------------------------------------------------
def instance_substantial():
    Duplicated.clear()
    current = bpy.context.window.scene.name

    act = utils.getActiveObj()
    matrix = Matrix(act.matrix_world)

    if act.instance_type != 'COLLECTION':
        return
    col = utils.collection.create('01_substantial')



    instance_substantial_loop( col , current )
    transform_apply()

    print('---------------------------------------------')
    utils.deselectAll()
    for ob in Duplicated:
        utils.select(ob,True)
        print(ob.name)
        utils.activeObj(ob)
        for mod in ob.modifiers:
            bpy.ops.object.modifier_apply( modifier = mod.name )

    bpy.ops.object.join()
    utils.getActiveObj().matrix_world = matrix

    act.matrix_world = matrix

    return utils.getActiveObj()


#---------------------------------------------------------------------------------------
#トランスフォームをアプライする
#スケールの正負判定　スケールに一つでも負の値が入っていたら法線をフリップする
#---------------------------------------------------------------------------------------
def transform_apply():
    act = utils.getActiveObj()
    if len( [ x for x in act.scale if x < 0 ] ) > 0:
        utils.mode_e()
        bpy.ops.mesh.flip_normals()
        utils.mode_o()
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True, properties=True)


#---------------------------------------------------------------------------------------
#コレクションインスタンスから元のコレクションを選択する
#カレントにコレクションがあるかどうか調べ、なければ別のシーンを検索する
#コレクションを返す
#---------------------------------------------------------------------------------------
def instance_select_collection():
    act = utils.getActiveObj()
    col = act.instance_collection

    utils.deselectAll()

    exist = False
    #カレントシーンにコレクションがあるかどうか調べる
    current_scn = bpy.context.window.scene
    exist = select_instance_collection_loop( col , current_scn.collection ,exist)

    #PARENTCOLLECTIONS.clear()
    #コレクションが見つからない場合、別のシーンを走査
    #見つかったら、シーンをアクティブにしてビューレイヤを表示状態にする
    if not exist:
        for scn in bpy.data.scenes:
            if current_scn != scn:
                exist = select_instance_collection_loop( col , scn.collection ,exist)

                if exist:
                    utils.sceneActive(scn.name)
                    break

    layer = bpy.context.window.view_layer.layer_collection
    show_collection_by_name( layer , col.name , False)
    collection_unhide_loop(layer,col)

    utils.deselectAll()
    collection = bpy.data.collections[col.name]
    for ob in collection.objects:
        utils.select(ob,True)
        utils.activeObj(ob)

    return collection

def collection_unhide_loop(layer ,col):
    show_collection_by_name( layer , col.name , False)
    for p in utils.collection.get_parent(col):
        if not utils.collection.isMaster( p ):
            collection_unhide_loop(layer , p )

#---------------------------------------------------------------------------------------
#Invert selected object using last selection.
#---------------------------------------------------------------------------------------
def invert_last_selection():
    amt = utils.getActiveObj()
    selected = utils.selected()
    matrix = Matrix(amt.matrix_world)
    matrix.invert()

    utils.deselectAll()

    for ob in selected:
        if ob != amt:
            m = ob.matrix_world
            ob.matrix_world = matrix @ m
            utils.act(ob)
            bpy.ops.object.transform_apply( location = True , rotation=True , scale=True )


#---------------------------------------------------------------------------------------
#ビューレイヤーを再帰的に調べて表示状態にする
#---------------------------------------------------------------------------------------
def select_instance_collection_loop( col ,current ,exist):
    props = bpy.context.scene.cyatools_oa
    children = current.children

    if children != None:
        for c in children:
            if col.name == c.name:
                exist = True

            exist = select_instance_collection_loop(col ,c, exist)

    return exist

#---------------------------------------------------------------------------------------
#ビューレイヤーを名前で表示状態切替
#---------------------------------------------------------------------------------------
def show_collection_by_name(layer ,name , state):
    props = bpy.context.scene.cyatools_oa
    children = layer.children

    if children != None:
        for ly in children:
            if name == ly.name:
                ly.hide_viewport = state

            show_collection_by_name(ly , name , state)


#---------------------------------------------------------------------------------------
#軸変換　まず　x->y　を作ってみる
#1．原点において意図する姿勢にしたあとapplyする
#2. 元の状態に戻す。この場合軸を入れ替えた状態のマトリックスにする
#---------------------------------------------------------------------------------------
def swap_axis(axis):
    act = utils.getActiveObj()
    matrix = act.matrix_world.to_3x3()
    pos = Vector(act.location)

    #第一段階
    #rotate direction : crockwize, view from the positive directon of the axis.
    if axis == 'x':
        m = Matrix(((1,0,0),(0,0,-1),(0,1,0)))
    elif axis == 'y':
        m = Matrix(((0,0,-1),(0,1,0),(1,0,0)))
    elif axis == 'z':
        m = Matrix(((0,-1,0),(1,0,0),(0,0,1)))

    m.transpose()
    act.matrix_world = m.to_4x4()
    bpy.ops.object.transform_apply( location = True , rotation=True , scale=True )


    #第二段階　転置して成分分離
    matrix.transpose()

    if axis == 'x':
        x =  matrix[0]
        y =  matrix[2]
        z = -matrix[1]

    elif axis == 'y':
        x =  matrix[2]
        y =  matrix[1]
        z =  -matrix[0]

    elif axis == 'z':
        x =  matrix[1]
        y = -matrix[0]
        z =  matrix[2]


    m = Matrix((x,y,z))

    m.transpose()
    act.matrix_world = m.to_4x4()
    act.location = pos

CONST_PARAM_LOC_SOURCE = ( ( -100, 100),( -100, 100 ),( -100, 100) )
CONST_PARAM_LOC_DEST = ( ( 100, -100),( -100, 100 ),( -100, 100) )
CONST_PARAM_ROT_SOURCE = ( ( -3.14, 3.14),( -3.14 , 3.14 ),( -3.14 , 3.14 ) )
CONST_PARAM_ROT_DEST = ( ( -3.14, 3.14),( 3.14 , -3.14 ),( 3.14 , -3.14 ) )

CONST_PARAM_LOC_DEST_Y = ( ( -100, 100),( 100, -100 ),( -100, 100) )
CONST_PARAM_ROT_DEST_Y = ( ( 3.14, -3.14),( -3.14 , 3.14 ),( 3.14 , -3.14 ) )

CONST_PARAM_LOC_DEST_Z = ( ( -100, 100),( -100, 100 ),( 100, -100) )
CONST_PARAM_ROT_DEST_Z = ( ( 3.14, -3.14),( 3.14 , -3.14 ),( -3.14 , 3.14 ) )


#---------------------------------------------------------------------------------------
#オブジェクトをインスタンスしてX軸でミラーコンストレインする
#---------------------------------------------------------------------------------------
def mirror(axis):
    props = bpy.context.scene.cyatools_oa
    if props.mirror_mode == 'const':
        for ob in utils.selected():
            utils.act(ob)
            ob_source = utils.getActiveObj()
            bpy.ops.object.duplicate_move_linked()

            ob_target = utils.getActiveObj()
            ob_target.matrix_world = Matrix()

            if axis == 'x':
                const_setting( ob_source , ob_target , CONST_PARAM_LOC_SOURCE , CONST_PARAM_LOC_DEST ,'LOCATION' ,'' )
                const_setting( ob_source , ob_target , CONST_PARAM_ROT_SOURCE , CONST_PARAM_ROT_DEST ,'ROTATION' ,'_rot')
                const_setting( ob_source , ob_target , CONST_PARAM_LOC_SOURCE , CONST_PARAM_LOC_DEST ,'SCALE' ,'_scale')

            if axis == 'y':
                const_setting( ob_source , ob_target , CONST_PARAM_LOC_SOURCE , CONST_PARAM_LOC_DEST_Y ,'LOCATION' ,'' )
                const_setting( ob_source , ob_target , CONST_PARAM_ROT_SOURCE , CONST_PARAM_ROT_DEST_Y ,'ROTATION' ,'_rot')
                const_setting( ob_source , ob_target , CONST_PARAM_LOC_SOURCE , CONST_PARAM_LOC_DEST_Y ,'SCALE' ,'_scale')

            if axis == 'z':
                const_setting( ob_source , ob_target , CONST_PARAM_LOC_SOURCE , CONST_PARAM_LOC_DEST_Z ,'LOCATION' ,'' )
                const_setting( ob_source , ob_target , CONST_PARAM_ROT_SOURCE , CONST_PARAM_ROT_DEST_Z ,'ROTATION' ,'_rot')
                const_setting( ob_source , ob_target , CONST_PARAM_LOC_SOURCE , CONST_PARAM_LOC_DEST_Z ,'SCALE' ,'_scale')


    elif props.mirror_mode == 'rot':
        for ob in utils.selected():
            utils.act(ob)
            #ob_source = utils.getActiveObj()
            bpy.ops.object.duplicate_move_linked()
            ob_target = utils.getActiveObj()
            ob_target.parent = None

            m = Matrix(ob_target.matrix_world)
            m.transpose()

            if axis == 'x':
                x = [ m[0][0],-m[0][1],-m[0][2] ,0]
                y = [-m[1][0], m[1][1], m[1][2] ,0]
                z = [-m[2][0], m[2][1], m[2][2] ,0]
                l = [-m[3][0], m[3][1], m[3][2] ,0]

            elif axis == 'y':
                x = [-m[0][0], m[0][1], m[0][2] ,0]
                y = [ m[1][0],-m[1][1],-m[1][2] ,0]
                z = [-m[2][0], m[2][1], m[2][2] ,0]
                l = [m[3][0], -m[3][1], m[3][2] ,0]

            elif axis == 'z':
                x = [ m[0][0], m[0][1],-m[0][2] ,0]
                y = [-m[1][0],-m[1][1], m[1][2] ,0]
                z = [ m[2][0], m[2][1],-m[2][2] ,0]
                l = [ m[3][0], m[3][1],-m[3][2] ,0]


            m_new =  Matrix([x,y,z,l])
            m_new.transpose()

            ob_target.matrix_world = m_new

    elif props.mirror_mode == 'normal':
        for ob in utils.selected():
            utils.act(ob)

            ob_source = utils.getActiveObj()
            bpy.ops.object.duplicate_move_linked()
            ob_target = utils.getActiveObj()
            ob_target.parent = None


            m = Matrix(ob_target.matrix_world)
            m.transpose()
            x = [-m[0][0], m[0][1], m[0][2] ,0]
            y = [-m[1][0], m[1][1], m[1][2] ,0]
            z = [-m[2][0], m[2][1], m[2][2] ,0]
            l = [-m[3][0], m[3][1], m[3][2] ,0]

            m_new =  Matrix([x,y,z,l])
            m_new.transpose()

            ob_target.matrix_world = m_new


def const_setting( ob_source , ob_target , source , dest , maptype , suffix ):
    constraint =ob_target.constraints.new('TRANSFORM')
    constraint.target = ob_source
    constraint.map_from = maptype
    constraint.map_to = maptype

    for x,val in zip(( 'x' , 'y' , 'z' ) , source ):
        exec('constraint.from_min_%s%s = %02f' % (x , suffix , val[0]) )
        exec('constraint.from_max_%s%s = %02f' % (x , suffix , val[1]) )

    for x,val in zip(( 'x' , 'y' , 'z' ),dest):
        exec('constraint.to_min_%s%s = %02f' % ( x , suffix , val[0]) )
        exec('constraint.to_max_%s%s = %02f' % ( x , suffix , val[1]) )

#---------------------------------------------------------------------------------------
#オブジェクトをインスタンスしてX軸で見た目を反転する
#---------------------------------------------------------------------------------------
def mirror_geom(axis):
    ob_source = utils.getActiveObj()
    bpy.ops.object.duplicate_move_linked()
    ob_target = utils.getActiveObj()
    ob_target.parent = None


    m = Matrix(ob_target.matrix_world)
    m.transpose()
    x = [-m[0][0], m[0][1], m[0][2] ,0]
    y = [-m[1][0], m[1][1], m[1][2] ,0]
    z = [-m[2][0], m[2][1], m[2][2] ,0]
    l = [-m[3][0], m[3][1], m[3][2] ,0]

    m_new =  Matrix([x,y,z,l])
    m_new.transpose()

    ob_target.matrix_world = m_new



#---------------------------------------------------------------------------------------
#replace
#---------------------------------------------------------------------------------------
def instance_replace():
    act_org = utils.getActiveObj()
    selected = utils.selected()

    for ob in selected:
        col_ob = ob.users_collection[0]
        p = ob.parent
        m = Matrix(ob.matrix_world)

        utils.act(act_org)
        bpy.ops.object.duplicate_move_linked()

        act_dup = utils.getActiveObj()
        act_dup.matrix_world = m
        act_dup.parent = p

        colections = act_dup.users_collection
        for c in colections:
            c.objects.unlink(act_dup)

        col_ob.objects.link(act_dup)

    for ob in selected:
        utils.delete(ob)


#---------------------------------------------------------------------------------------
# add bones at the selected objects
#---------------------------------------------------------------------------------------
class AddBoneObj():
    def __init__( self , ob ):
        m = Matrix(ob.matrix_world)
        m.transpose()
        self.x = [ m[0][0], m[0][1], m[0][2] ]
        self.y = [ m[1][0], m[1][1], m[1][2] ]
        self.z = Vector([ m[2][0], m[2][1], m[2][2] ])
        self.head = Vector([ m[3][0], m[3][1], m[3][2] ])

        self.name = ob.name

        self.axis_forward = {}

        self.axis_forward['X']  = Vector([ m[0][0], m[0][1], m[0][2] ])
        self.axis_forward['-X'] = Vector([ -m[0][0], -m[0][1], -m[0][2] ])
        self.axis_forward['Y']  = Vector([ m[1][0], m[1][1], m[1][2] ])
        self.axis_forward['-Y'] = Vector([ -m[1][0], -m[1][1], -m[1][2] ])
        self.axis_forward['Z'] = Vector([ m[2][0], m[2][1], m[2][2] ])
        self.axis_forward['-Z']  = Vector([ -m[2][0], -m[2][1], -m[2][2] ])


def add_bone():
    props = bpy.context.scene.cyatools_oa
    amt = utils.getActiveObj()

    af = props.axis_forward
    au = props.axis_up

    m_array = []
    for ob in utils.selected():
        if ob != amt:
            m_array.append( AddBoneObj(ob) )

    utils.act(amt)
    utils.mode_e()

    for m in m_array:
        b = amt.data.edit_bones.new( m.name )
        b.head = m.head
        #b.tail = m.head + m.z
        b.tail = m.head + m.axis_forward[ af ]
        print(m.axis_forward[ af ])
        bpy.ops.armature.select_all(action='DESELECT')


# First, select object next select armature. Enter edit mode and select bone to align.
def snap_bone_at_obj():
    amt = utils.getActiveObj()
    bone = utils.get_active_bone()

    for ob in utils.selected():
        if ob != amt:
            loc = ob.location

    bone.head = loc


#---------------------------------------------------------------------------------------
#ロケータを配置して分離したいフェースを選択　実行するとフェースが複製されロケータの位置が原点になって配置される
#---------------------------------------------------------------------------------------
def separate_face():
    objects = set([ob.name for ob in utils.selected()])
    bpy.ops.mesh.duplicate_move()
    bpy.ops.mesh.separate(type='SELECTED')

    utils.mode_o()

    dupulicated = []
    for ob in utils.selected():
        if ob.name not in objects:
            dupulicated.append(ob)
            print(ob.name)

    bpy.ops.object.select_all(action='DESELECT')

    utils.act(dupulicated[0])
    for ob in dupulicated:
        utils.select(ob,True)

    bpy.ops.object.join()










