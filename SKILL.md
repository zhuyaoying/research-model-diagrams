---
name: research-model-diagrams
description: "Create and refine research model diagrams from code, method descriptions, or existing figures: hierarchical overview and module details, visible tensor shapes, intermediate feature representations, mathematical operators, and verified paper-figure references. Use for 科研模型绘图、总览图与核心算法图、维度变化可视化、模型图打磨、PPT 手工重画参考. Also discuss module grouping or naming within an ongoing diagram task without editing when requested. Do not use as the primary owner of result charts, whole slide decks, or standalone novelty reviews."
license: MIT
metadata:
  version: "1.0.0"
---

# 科研模型绘图 · Research Model Diagrams

把真实计算过程转换为可检查、可重画的科研模型图。优先满足四件事：**模块有层级、数据有形态、运算有语义、文献有出处**。

这是独立 Skill，不要求安装 CCFA、指定 MCP 服务或固定图像模型。遵守宿主系统的工具与权限规则。用户当前要求覆盖这里的默认偏好。

## 工作边界

- **绘图或修改**：创建/修改当前主图与相应源文件；不改模型代码、数据、参数或实验结论。
- **只讨论**：用户说“不改图”“解释输出”“如何组合模块”时，只分析和回答，不重绘、不改源图。
- **只找参考**：给出部分—论文—图号—改绘方式的映射，不自动生成多张草案。
- **创新性核对**：只有用户要求时才检索已有工作；模块重组和重新命名不能证明独创性。较大的文献评审应单独处理，不悄悄扩展普通绘图任务。

## 默认交付偏好

1. 默认一张**模型总览图**＋一张**核心算法组件图**；按实际内容调整，不强行凑三块或六块。
2. 总览图显示真实输入、核心模块、分支、融合与各自输出。组件图展开总览里的模块，沿用相同 ID、名称、颜色与接口。
3. 维度文字与图形表示同时存在：矩阵网格、特征列条、token、张量切片、mask 或曲线，按对象类型选择。
4. 运算发生在明确节点上；两条输入分别接入操作符，输出再连到结果。箭头仅表示流向。
5. 优先编辑已有矢量/代码源；精确数学图优先确定性 SVG 或可编辑 PPTX。图像生成适合布局/风格探索或用户要求的位图，按宿主工具规定调用。
6. 一份内容的 PNG 预览和 SVG/PPTX 源文件属于同一版。原位更新规范文件名；仅在用户要求比较时生成多个设计版本。
7. 用户手工画 PPT 时，交付可照着画的参考和说明即可，不强制额外生成完整演示文稿。

## 执行流程

### 1. 确认本轮动作与方法依据

先判断本轮是绘图、改图、讨论还是找参考。复用此前已确认的信息。

从用户指明的最终代码、配置、方法文本提取计算图；现有图片提供视觉依据，不能覆盖已确认的方法语义。若代码与论文冲突，指出具体位置，先完成不受影响的工作。缺少关键输入/输出或连接关系时，询问最小必要问题；未知数值维度可暂用有定义的符号，不能臆造。

开始绘图时读取 [method-contract.md](references/method-contract.md)。建立简短的节点、边、张量和输出清单。检查特征分组是否真是可学习的选择器，避免把预处理重新包装成算法。

### 2. 先定层级，再定版式

总览回答“整个模型怎样得到各个预测”；细节回答“核心模块内部怎样计算”。组件图的局部输入/输出必须能映射回总览的模块边界。

按机制目的组织模块，不按矩形数量判定贡献。若讨论命名或创新性，遵循 method-contract 中的“模块与贡献”规则。

### 3. 使用论文图形语法

用户要论文参考时，读取 [reference-mapping.md](references/reference-mapping.md)。核验具体论文版本、图号与图中内容，输出逐模块映射。已有已核验的来源不必每次改图都重新检索。

借鉴输入表现、分支布局、张量层次和运算节点表达，不移植参考论文中本模型没有的模块。

### 4. 画数据与运算

读取 [visual-grammar.md](references/visual-grammar.md)。显示重要转换前后形状、轴含义和必要 dtype。细节图展开核心公式涉及的中间表示；总览保留模块边界维度。

可用 [operator-legend.svg](assets/operator-legend.svg) 作为统一运算节点样式。图例中的圆内十字、斜叉、实心点分别约定为逐元素加法、矩阵乘法、Hadamard 乘法；这不是所有数学语境通用的定义。

### 5. 渲染与修订

读取 [rendering-revisions.md](references/rendering-revisions.md)。先记录当前正确内容，再执行本轮差异。新增符号不能移除维度；补维度不能把矩阵、曲线和 token 全部退化成文字框。

生成后检查实际渲染图：连接是否完整、标签是否遮挡、操作数是否独立进入节点、输出有没有错误合并。只看源代码不能算视觉检查。宿主无法预览时明确说明未完成视觉验证。

如图中有较多矩阵运算，可选择使用 [check_shapes.py](scripts/check_shapes.py) 检查声明的形状；先看 [shape-checker.md](references/shape-checker.md)。它不验证模型真实性，也不能代替视觉检查。

### 6. 交付

先给当前图或讨论结论，再简述已修正内容和确实未解决的问题。文件交付时指向最新规范文件与可编辑源；不堆叠中间稿。

默认图稿名称：`overview.svg` / `overview.png`、`modules.svg` / `modules.png`。若项目已有命名，沿用原名。方法契约和参考映射合并在一份简短 `figure-notes.md`，无需为简单改动创建一套审计目录。

## 可复用 Prompt

需要完整绘图要求、定向改图、只查参考或只讨论的用户提示词时，读取 [prompt-library.md](references/prompt-library.md)。填入实际方法信息；模板中的示例和变量不能成为模型事实。
