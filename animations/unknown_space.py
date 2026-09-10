"""Render with Manim Community 0.20.1 / Cairo; no GPU or LaTeX required."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from manim import *
from evidence_story import build_story, RESOLUTION, CAMERAS, START, GOAL

INK='#173847'; MUTED='#496574'; FREE='#79c7c1'; OCC='#d36b53'; UNKNOWN='#e7d49b'
FONT='Microsoft JhengHei'

class SwapText(Animation):
    """Cross-fade whole Chinese labels instead of morphing individual glyphs."""
    def __init__(self, mobject, replacement, **kwargs):
        self.before = mobject.copy()
        self.after = replacement.copy()
        super().__init__(mobject, **kwargs)

    def interpolate_mobject(self, alpha):
        self.mobject.become(self.before if alpha < .5 else self.after)
        self.mobject.set_opacity(abs(2 * alpha - 1))

class UnknownIsNotFree(Scene):
    def construct(self):
        self.camera.background_color='#eef3f6'
        grids, results, candidate, rays=build_story()
        def text(value,size=24,color=INK):
            return Text(value,font=FONT,font_size=size,color=color)
        def point(cell):
            return np.array([-5.7+(cell[0]+.5)*.24,-2.45+(cell[1]+.5)*.24,0])
        def state_layer(states):
            return VGroup(*[Square(side_length=.233,stroke_width=0,fill_opacity=1,
                                   fill_color={-1:UNKNOWN,0:FREE,1:OCC}[int(states[x,z])]).move_to(point((x,z)))
                            for x in range(32) for z in range(20)])
        def route(cells,color):
            return VMobject(stroke_color=color,stroke_width=5).set_points_as_corners([point(c) for c in cells])
        title=text('未知，不是自由空間',38).to_edge(UP,buff=.35).align_to(np.array([-6.5,0,0]),LEFT)
        subtitle=text('CareSpace 3D  /  觀測如何改變通行證據',21,MUTED).next_to(title,DOWN,buff=.15).align_to(title,LEFT)
        boundary=Rectangle(width=7.8,height=4.92,stroke_color='#aec0c9',stroke_width=1).move_to(point((15.5,9.5)))
        base=state_layer(grids[0].states)
        self.add(title,subtitle,boundary,base)
        legend=VGroup(*[VGroup(Square(.17,fill_color=c,fill_opacity=1,stroke_width=0),text(t,19)).arrange(RIGHT,buff=.1) for t,c in [('自由',FREE),('障礙',OCC),('未知',UNKNOWN)]]).arrange(RIGHT,buff=.4).move_to([-1.8,-2.85,0])
        foot=text('原理解說・原創 2D 場景・非研究成果截圖',18,MUTED).to_edge(DOWN,buff=.2)
        self.add(legend,foot)
        markers=VGroup()
        for c,label,color in [(START,'S',INK),(GOAL,'G','#a44030')]:
            loc=point(c)
            markers.add(Circle(radius=.12,stroke_color=color,stroke_width=3).move_to(loc),text(label,22,color).move_to(loc+UP*.29))
        markers.set_z_index(5);self.add(markers)
        panel=RoundedRectangle(width=3.7,height=4.65,corner_radius=.12,fill_color=WHITE,fill_opacity=1,stroke_width=0).move_to([4.25,-.04,0]);self.add(panel)
        step=text('01  尚未觀測',24).move_to([4.25,1.78,0])
        verdict=text('未知',40,'#85621b').move_to([4.25,.92,0])
        explanation=text('沒有觀測證據\n就不能確認通路',23).move_to([4.25,-.06,0])
        detail=text('S：起點   G：終點\n色塊：離散空間證據',19,MUTED).move_to([4.25,-1.37,0])
        self.add(step,verdict,explanation,detail);self.wait(2.5)
        def camera_marker(index):
            return Triangle(fill_color='#285e9d',fill_opacity=1,stroke_width=0).scale(.13).rotate(-PI/2).move_to(point(CAMERAS[index])).set_z_index(6)
        cam1=camera_marker(0)
        self.play(FadeIn(cam1),SwapText(step,text('02  第一個視角',24).move_to(step)),run_time=.8)
        ray1=VGroup(*[Line(point(o-.5),point(e-.5),stroke_color='#398ca0',stroke_width=1.3,stroke_opacity=.6) for o,e in rays[0][::24] if e is not None])
        self.play(LaggedStart(*[Create(l) for l in ray1],lag_ratio=.035),run_time=2)
        layer1=state_layer(grids[1].states)
        self.play(FadeIn(layer1),FadeOut(ray1),SwapText(explanation,text('射線經過處：自由\n命中位置：障礙',23).move_to(explanation)),run_time=1.4)
        self.wait(2)
        dashed=DashedVMobject(route(candidate,'#946d20'),num_dashes=38).set_z_index(4)
        self.play(Create(dashed),SwapText(step,text('03  遮擋後仍未知',24).move_to(step)),SwapText(explanation,text('虛線只是候選路線\n不代表已確認可走',23).move_to(explanation)),run_time=1.5)
        self.wait(3)
        cam2=camera_marker(1)
        self.play(FadeIn(cam2),SwapText(step,text('04  補上另一視角',24).move_to(step)),run_time=.8)
        ray2=VGroup(*[Line(point(o-.5),point(e-.5),stroke_color='#398ca0',stroke_width=1.3,stroke_opacity=.6) for o,e in rays[1][::24] if e is not None])
        self.play(LaggedStart(*[Create(l) for l in ray2],lag_ratio=.035),run_time=2)
        layer2=state_layer(grids[2].states)
        self.play(FadeIn(layer2),FadeOut(ray2),FadeOut(dashed),run_time=1.3)
        # Path is produced by the existing conservative planner, not authored coordinates.
        cells=[np.array(p)/RESOLUTION-.5 for p in results[2]['path']]
        solid=route(cells,'#075f62').set_z_index(4)
        self.play(Create(solid),SwapText(verdict,text('可通行',38,'#075f62').move_to(verdict)),SwapText(explanation,text('新的觀測補足證據\n自由空間形成通路',23).move_to(explanation)),run_time=1.5)
        self.wait(3)
        self.play(SwapText(step,text('先有證據，再下判斷',23).move_to(step)),SwapText(detail,text('使用既有通行規劃器\n2D 示意，非輪椅驗證',19,MUTED).move_to(detail)),run_time=.8)
        self.wait(3)
