"""CPU Cairo explanation of configuration-space inflation, using the real planner."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from manim import *
from unknown_space import SwapText, FONT, INK, MUTED, FREE, OCC, UNKNOWN
from footprint_story import build_footprint_story, RADII
from evidence_story import START, GOAL, RESOLUTION

INFLATED = '#ac98c4'

class FootprintChangesPassage(Scene):
    def construct(self):
        self.camera.background_color = '#eef3f6'
        grid, states, results = build_footprint_story()
        def text(value, size=24, color=INK):
            return Text(value, font=FONT, font_size=size, color=color, line_spacing=.8)
        def point(cell):
            return np.array([-5.7+(cell[0]+.5)*.24, -2.45+(cell[1]+.5)*.24, 0])
        def layer(state):
            def color(x,z):
                raw = grid.states[x,z]
                if raw == 1: return OCC
                if raw == -1: return UNKNOWN
                return INFLATED if state[x,z] == 1 else UNKNOWN if state[x,z] == -1 else FREE
            return VGroup(*[Square(.233, stroke_width=0, fill_opacity=1,
                                  fill_color=color(x,z)).move_to(point((x,z)))
                            for x in range(32) for z in range(20)])
        def route(result):
            cells = [grid.cell(p) for p in result['path']]
            return VMobject(stroke_color='#075f62', stroke_width=5).set_points_as_corners(
                [point(c) for c in cells]).set_z_index(4)
        title = text('同一個空間，尺寸改變通路',36).to_edge(UP,buff=.35).align_to(np.array([-6.5,0,0]),LEFT)
        subtitle = text('CareSpace 3D  /  固定觀測與端點，只改圓形足跡半徑',21,MUTED).next_to(title,DOWN,buff=.15).align_to(title,LEFT)
        self.add(title,subtitle,layer(grid.states))
        legend = VGroup(*[VGroup(Square(.17,fill_color=c,fill_opacity=1,stroke_width=0),text(t,19)).arrange(RIGHT,buff=.1)
                          for t,c in [('自由',FREE),('原障礙',OCC),('中心禁入',INFLATED),('未知',UNKNOWN)]]).arrange(RIGHT,buff=.25).move_to([-1.8,-2.85,0])
        footer = text('原創 2D 解說・離散圓形足跡模型・非輪椅或高度驗證',18,MUTED).to_edge(DOWN,buff=.2)
        self.add(legend,footer)
        for cell,label in [(START,'S'),(GOAL,'G')]:
            self.add(Dot(point(cell),radius=.05,color=INK).set_z_index(7),
                     text(label,22).move_to(point(cell)+UP*.32).set_z_index(7))
        panel = RoundedRectangle(width=3.7,height=4.85,corner_radius=.12,fill_color=WHITE,fill_opacity=1,stroke_width=0).move_to([4.25,-.04,0])
        step = text('01  原始觀測',24).move_to([4.25,1.9,0])
        radius_label = text('半徑 0.12 m',30).move_to([4.25,1.16,0])
        verdict = text('先考慮物體大小',25).move_to([4.25,.49,0])
        explanation = text('不能只看中心線\n物體本身也要避障',23).move_to([4.25,-.35,0])
        detail = text('格距 0.20 m\n保守餘量約 0.283 m\n膨脹距離＝半徑＋餘量',18,MUTED).move_to([4.25,-1.5,0])
        self.add(panel,step,radius_label,verdict,explanation,detail)
        body = Circle(radius=RADII[0]*.24/RESOLUTION,stroke_color=INK,stroke_width=3,fill_color=WHITE,fill_opacity=.6).move_to(point(START)).set_z_index(6)
        self.add(body); self.wait(2.5)
        self.play(FadeIn(layer(states[0])),SwapText(step,text('02  膨脹障礙與邊界',22).move_to(step)),
                  SwapText(verdict,text('可通行',36,'#075f62').move_to(verdict)),
                  SwapText(explanation,text('紫色：中心不可進入\n沿剩餘自由格找通路',22).move_to(explanation)),run_time=1.2)
        path = route(results[0]); self.play(Create(path),run_time=1.3)
        self.play(MoveAlongPath(body,path),run_time=3,rate_func=linear); self.wait(1)
        self.play(FadeOut(path),body.animate.move_to(point(START)),run_time=.6)
        larger = Circle(radius=RADII[1]*.24/RESOLUTION,stroke_color=INK,stroke_width=3,fill_color=WHITE,fill_opacity=.6).move_to(point(START)).set_z_index(6)
        self.play(FadeIn(layer(states[1])),Transform(body,larger),
                  SwapText(step,text('03  加大圓形足跡',24).move_to(step)),
                  SwapText(radius_label,text('半徑 0.25 m',30).move_to(radius_label)),
                  SwapText(explanation,text('禁入範圍擴大\n目前仍有連通路徑',23).move_to(explanation)),run_time=1.2)
        path2=route(results[1]); self.play(Create(path2),run_time=1.2)
        self.play(MoveAlongPath(body,path2),run_time=3,rate_func=linear); self.wait(1)
        self.play(FadeOut(path2),body.animate.move_to(point(START)),run_time=.6)
        largest = Circle(radius=RADII[2]*.24/RESOLUTION,stroke_color=INK,stroke_width=3,fill_color=WHITE,fill_opacity=.6).move_to(point(START)).set_z_index(6)
        self.play(FadeIn(layer(states[2])),Transform(body,largest),
                  SwapText(step,text('04  通路不再連通',24).move_to(step)),
                  SwapText(radius_label,text('半徑 0.35 m',30).move_to(radius_label)),
                  SwapText(verdict,text('阻斷',36,'#a44030').move_to(verdict)),
                  SwapText(explanation,text('起終點仍是自由格\n中間已沒有可用通路',22).move_to(explanation)),run_time=1.4)
        self.wait(3)
        self.play(SwapText(step,text('判定必須附上尺寸',23).move_to(step)),
                  SwapText(explanation,text('同一份觀測證據\n不同尺寸，不同答案',22).move_to(explanation)),run_time=.8)
        self.wait(3)
