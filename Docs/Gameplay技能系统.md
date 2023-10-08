# Gameplay技能系统

- 技能、任务、属性和效果
  - Gameplay技能 实为继承自 UGameplayAbility 类的C++类或蓝图类。其定义C++代码或蓝图脚本中技能的实际作用，并建立处理技能的元素，如复制和实例化行为。
  - 在定义技能的逻辑过程中，gameplay技能中的逻辑通常会调用一系列被称为 技能任务 异步编译块。技能任务衍生自抽象 UAbilityTask 类，以C++编写。其完成操作时，会基于最终结果频繁调用委托（C++中）或输出执行引脚（蓝图中）
  - 除Gameplay技能外，Gameplay技能系统还支持 Gameplay属性 和 Gameplay效果。
    - Gameplay属性是存储在 FGameplayAttribute 结构中的"浮点"值，将对游戏或Actor产生影响；其通常为生命值、体力、跳跃高度、攻击速度等值。
    - Gameplay效果可即时或随时间改变Gameplay属性（通常称为"增益和减益"）。例如，施魔法时减少魔法值，激活"冲刺"技能后提升移动速度，或在治疗药物的效力周期内逐渐恢复生命值。
  - 与Gameplay技能系统交互的Actor须拥有 技能系统组件。此组件将激活技能、存储属性、更新效果，和处理Actor间的交互。启用Gameplay技能系统并创建包含技能系统组件的Actor后，便可创建技能并决定Actor的响应方式。
- 要使用此系统的全部功能，添加"GameplayAbilities"、"GameplayTags"和"GameplayTasks"到项目的"(ProjectName).Build.cs"文件中的 PublicDependencyModuleNames 中。

## 技能系统组件与属性

- 技能系统组件 (UAbilitySystemComponent) 是Actor和 游戏玩法技能组件（Gameplay Ability System） 之间的桥梁。Actor需要拥有自己的技能系统组件，或可以使用其它Actor的技能系统组件，才能与游戏玩法技能系统进行互动。
  - 要建立`AActor`子类来使用游戏玩法技能系统，请先执行`IAbilitySystemInterface`接口并覆写`GetAbilitySystemComponent`函数。此函数必须返回到Actor相关的技能系统组件。
  - 在大多数情况下，Actor类会有一个变量，并且有一个`UPROPERTY`标记，其中会存储一个到技能系统组件的指向器，类似于任何Actor类型中内置的其它组件。虽然Actor通常会有自己的技能系统组件，但是有些情况下，你会想要部分Actor（例如玩家的Pawn或角色）使用其它Actor（例如玩家状态或玩家控制器）拥有的技能系统组件。这种情况一般涉及到玩家分数或者长期存在的技能冷却计时器，因为即便是玩家的Pawn或角色被销毁并重生，或者玩家拥有一个新的Pawn或角色，这些内容也不会重置。游戏玩法技能系统便可以支持此行为；如果你需要使用它，就要编写Actor的`GetAbilitySystemComponent`函数，从而让它返回到你想要使用的技能系统组件。

## 玩法技能

- 玩法技能（Gameplay Ability） 源自`UGameplayAbility`类，定义了游戏中技能的效果、使用技能付出的代价（如有），以及何时或在何情况下可以使用等。
  - 玩法技能可以作为异步运行的实例化对象存在，因此你可以运行专门的多阶段任务，包括角色动画、粒子和声效，乃至根据执行时的用户输入或角色交互设计分支。玩法技能可以在整个网络中自我复制，运行在客户端或服务器计算机上（包括客户端预测支持），甚至还能同步变量和执行远程过程调用（RPC）。玩法技能还使引擎可在游戏会话期间灵活实现游戏技能，例如提供的扩展功能可用于实现冷却和使用消耗、玩家输入、使用动画蒙太奇的动画，以及对给予Actor的技能本身做出反应。

- 授予和撤销技能
  - 在Actor可以使用某项技能之前，必须向其技能系统组件授予该技能。技能系统组件的以下函数可以授予对某项技能的访问：
    - GiveAbility：使用 FGameplayAbilitySpec 指定要添加的技能，并返回 FGameplayAbilitySpecHandle。
    - GiveAbilityAndActivateOnce：使用 FGameplayAbilitySpec 指定要添加的技能，并返回 FGameplayAbilitySpecHandle。技能必须实例化，并且必须能够在服务器上运行。尝试在服务器上运行技能后，将返回 FGameplayAbilitySpecHandle。如果技能没有满足所需条件，或者无法执行，返回值将无效，并且技能系统组件将不会被授予该技能。
  - 以下函数可以利用授予技能后返回的 FGameplayAbilitySpecHandle，来撤销对技能系统组件中该技能的访问。
    - ClearAbility: 从技能系统组件中移除指定技能。
    - SetRemoveAbilityOnEnd：当该技能执行完毕时，将该技能从技能系统组件中移除。如果未执行该技能，将立即移除它。如果正在执行该技能，将立即清除其输入，这样玩家就无法重新激活它或与它互动。
    - ClearAllAbilities：从技能系统组件中移除所有技能。此函数是唯一不需要 FGameplayAbilitySpecHandle 的函数。

- 基本用法
  - 将玩法技能授予Actor的技能系统组件后，玩法技能的基本执行生命周期如下：
    - 即使调用者没有尝试执行某项技能，`CanActivateAbility`也可以让调用者知道是否可执行该技能。例如，您可以在户界面上将玩家无法使用的图标变成灰色并停用这些图标，或者对角色播放声音或粒子效果来显示某项技能是否可用。
    - `CallActivateAbility`执行技能相关的游戏代码，但不会检查该技能是否可用。通常在 `CanActivateAbility`检查及执行技能之间需要某些逻辑时才会调用该函数。
      - 用户需要使用技能的定制功能覆盖的主代码要么是名为`ActivateAbility`的C++函数，要么是名为Activate Ability的蓝图事件。
      - 与Actor和组件不同，玩法技能不会使用"tick"函数完成主要工作，而是在激活过程中启动技能任务，异步完成大部分工作，然后连接代理（在C++中）以处理这些任务的输出，或者连接节点以输出执行引脚（在蓝图中）。
      - 如果从"激活"中调用`CommitAbility`函数，它将应用执行技能的消耗，例如从玩法属性中减去资源（例如"魔法值"、"体力值"或游戏系统所用的任何其他资源）和应用冷却。
      - `CancelAbility`提供了取消技能的机制，不过技能的`CanBeCanceled`函数可以拒绝请求。与`CommitAbility`不同，该函数可供技能外调用者使用。成功的取消先播放给On Gameplay Ability Cancelled，然后通过标准代码路径结束技能，让技能可运行特殊的清理代码，否则取消时的行为将与自行结束时的行为不同。
    - TryActivateAbility 是执行技能的典型方式。该函数调用 CanActivateAbility 来确定技能是否可以立即运行，如果可以，则继续调用 CallActivateAbility。
    - EndAbility （C++）或End Ability节点（蓝图）会在技能执行完毕后将其关闭。如果技能被取消，UGameplayAbility 类会将其作为取消流程的一部分自动处理，但其他情况下，开发者都必须调用C++函数或在技能的蓝图图表中添加节点。如果未能正常结束技能，将导致玩法技能系统认为技能仍在运行，从而带来一些影响，例如禁止将来再使用该技能或任何被该技能阻止的技能。

- 标记
  - 玩法标记 有助于确定玩法技能之间的交互方式。每种技能都拥有一组标记，以可影响其行为的方式识别和分类技能，还有玩法标记容器和游戏标记查询，用于支持与其他技能进行交互。

- 复制
- 玩法技能支持复制内蕴状态和玩法事件，或关闭复制以节省网络带宽和缩短CPU周期。技能的 玩法技能复制策略（Gameplay Ability Replication Policy） 可以设置为"是"或"否"，这控制着技能是否复制自身实例、更新状态或跨网络发送玩法事件。对于复制技能的多人游戏，你可以选择复制的处理方式，这些选项被称为 玩法网络执行策略（Gameplay Net Execution Policy）：
  - 本地预测：（Local Predicted:）此选项有助于在响应能力和准确性之间实现良好的平衡。在本地客户端发出命令后，技能将立即在客户端上运行，但服务器起着决定性作用，并且可以根据技能的实际影响来覆盖客户端。客户端实际上是从服务器请求执行"技能"的权限，但也在本地进行处理，就像服务器需要同意客户端对结果的看法一样。因为客户端在本地预测技能的行为，所以只要客户端的预测与服务器不矛盾，它就会非常顺利地运行且无滞后。
  - 仅限本地：（Local Only:）客户端仅在本地运行技能。如果使用服务器的客户端是主机（在物理服务器计算机上播放）或者是在单人游戏中，尽管技能将在服务器上运行，也不会对服务器应用复制。这种情况不适用于专用服务器游戏，因为在专用服务器游戏中客户端永远不会在服务器计算机上运行。客户端通过该技能带来的任何影响都将继续遵循常规复制协议，包括可能从服务器接收更正。
  - 服务器启动：（Server Initiated:）在服务器上启动的技能将传播到客户端。从客户端的角度来看，这可以更准确地复制服务器上实际发生的情况，但使用技能的客户端会因缺少本地预测而发生延迟。虽然这种延迟非常短，但某些类型的技能（特别是在压力情况下快速执行的操作）将不会像在本地预测模式中那样顺畅。
  - 仅限服务器：（Server Only:）"仅限服务器"技能将在服务器上运行，不会复制到客户端。被这些技能修改的任何变量都将像往常一样进行复制，这意味着该技能能够影响服务器的权威数据，并会将影响传递给客户端。以这种方式，技能仍然可以影响客户端的观察，尽管技能本身只在服务器上运行。

- 实例化策略
在执行玩法技能时，通常会产生一个（技能类型的）新对象，用于跟踪正在进行的技能。由于在某些情况下可能会非常频繁地执行技能，例如在大逃杀、MOBA、MMO或RTS游戏中一百个或更多玩家与AI角色之间的战斗，可能会出现快速创建技能对象对性能产生负面影响的情况。为了解决这个问题，技能可以选择三种不同的实例化策略，以在效率和功能之间达到平衡。支持的三种实例化类型：
  - 按执行实例化：（Instanced per Execution:）每次技能运行时，都会产生技能对象的副本。这样做的优点是可以自由使用蓝图图表和成员变量，并且所有内容都将在执行开始时初始化为默认值。这是最简单的实例化策略，但由于开销较大，该策略更适合不会频繁运行的技能。例如，MOBA中的"终极技能"可以使用该策略，因为两次执行之间存在较长的冷却时间（通常为60-90秒），并且只有少数几个角色（通常约为10个）使用这些技能。由计算机控制的"小兵"使用的基本攻击技能就不能使用该策略，因为可能同时存在数百个"小兵"，每个都可以频繁地发出基本攻击，从而导致快速创建（或者复制）新对象。
  - 按Actor实例化：（Instanced per Actor:）在技能首次执行时，每个Actor会生成该技能的一个实例，该对象会在以后的执行中重复使用。这就要求在两次技能执行之间清理成员变量，同时也使保存多个执行的信息成为可能。按Actor是较为理想的复制方法，因为技能具有可处理变量和RPC的复制对象，而不是浪费网络带宽和CPU时间，在每次运行时产生新对象。该策略适用于大规模的情况，因为大量使用技能的Actor（例如在大型战斗中）只会在第一次使用技能时产生对象。
  - 非实例化：（Non-Instanced:）这是所有类别中最高效的实例化策略。在运行时，技能不会生成任何对象，而是使用类默认对象。但是，在高效的同时也伴随着一些限制。首先，该策略特别要求技能完全用C ++编写，因为创建蓝图图表需要对象实例。你可以创建非实例化技能的蓝图类，但这只能更改已公开属性的默认值。此外，在执行技能期间，即使在本机C ++代码中，技能也不能更改成员变量，不能绑定代理，也不能复制变量或处理RPC。该策略仅适用于不需要内部变量存储（尽管可以针对技能用户设置属性）并且不需要复制任何数据的技能。它尤其适合频繁运行且被许多角色使用的技能，例如大型RTS或MOBA作品中部队使用的基本攻击。

- 触发玩法事件
  - 玩法事件（Gameplay Events） 是可以传递的数据结构，能够直接触发玩法技能，无需通过正常通道，即可根据情境发送数据有效负载。常用的方法是调用Send Gameplay Event To Actor并提供实施`IAbilitySystemInterface`接口的Actor和玩法事件所需的情境信息，但也可以直接在技能系统组件上调用Handle Gameplay Event。因为这不是调用玩法技能的正常方式，所以技能可能需要的情境信息将通过`FGameplayEventData`数据结构传递。该结构是一种通用结构，不会针对任何特定的玩法事件或技能进行扩展，但应该能够满足任何用例的要求。多态`ContextHandle`字段会根据需要提供其他信息。
    - 当游戏事件触发玩法技能时，玩法技能不会通过激活技能代码路径运行，而是使用提供附加情境数据作为参数的"从事件激活技能"（Activate Ability From Event）。如果希望技能响应游戏事件，请务必处理此代码路径，同时还应注意，一旦在玩法技能的蓝图中实施，"从事件激活技能"（Activate Ability From Event）将取代"激活技能"（Activate Ability），让所有激活流量通过自身。

## 游戏属性及游戏效果

- 游戏性属性
  - 游戏性属性 包括可以通过单浮点数值描述的Actor当前状态的任何数值度量，例如，生命值、体力、移动速度和魔法抗性等等。属性作为 FGameplayAttribute 类型的UProperty在 属性集 中声明，属性集包含属性并监视对它们的任何修改尝试。
  - 要创建属性集，应从 UAttributeSet 继承，然后添加使用 UPROPERTY 标记的游戏性属性数据成员。
  - 创建好属性集之后，必须向技能系统组件注册它。可以将属性集添加为拥有技能系统组件的Actor的子对象，或者将它传递给技能系统组件的`GetOrCreateAttributeSubobject`函数。

- 游戏性效果
  - 游戏性效果是游戏性技能系统更改属性的方法。其中包括：
    - 指示对属性的底数值进行更改，例如，当某个Actor受到伤害时，减小其生命值。
    - 临时更改（通常称为"增益"或"减益"），例如，使移动速度提升几秒。
    - 随时间推移而应用的永久性更改，例如在几秒钟的时间段内（或无限期地）每秒重新生成特定数量的魔法值。
  - 游戏性效果实现为可与技能系统组件交互且适当时可在它们处于激活状态时在其中存储的仅数据蓝图（属于`UGameplayEffect`基类）。

- 主要属性
  - 与大多数游戏性技能系统的其他部分不同，无论在本机还是蓝图代码中，游戏性效果通常不覆盖基类`UGameplayEffect`。相反，游戏性效果被设计成完全通过变量来配置。以下是部分可以调整的游戏性效果的主要属性：
    - 时长：游戏性效果可立即应用（例如，受到攻击时生命值减少），在有限期间内应用（例如，持续时间为几秒的移动速度提升），或无限期地应用（例如，随着时间的推移，某个角色自然地恢复法力值）。另外，具有非瞬间时长的效果也可以按不同的间隔应用自身。这不仅对于更改效果在Gameplay方面产生作用的方式非常有用，对于设置重复音频或视觉效果等的时机方面也非常有用。
    - 修饰符和执行（Execution）：修饰符会确定游戏性效果与属性交互的方式。其中包括与属性自身的数学上的交互，例如，"将防御力提升5%"，以及执行效果的游戏性标记要求。当需要让某个游戏性效果产生超出修饰符支持范围的影响时，需要用到"执行（Execution）"。"执行（Execution）"使用`UGameplayEffectExecutionCalculation`来定义游戏性效果执行时它具有的自定义行为。定义修饰符无法充分覆盖的复杂方程式时，它们特别有用。
    - 应用要求：应用要求包括游戏性效果应用时必须存在（或被禁止）的多组游戏性标记以及游戏性效果不应用的随机概率。如果这些要求无法满足游戏的需求，可以从`UGameplayEffectCustomApplicationRequirement`基类派生数据对象，在其中你可以编写可任意定义复杂应用规则的本地代码。
    - 授予技能：应用时，游戏性效果不仅可以授予游戏性标记，还可以授予技能。当与"执行（Execution）"配合使用时，可将它们用于设置高度特殊的游戏性组合。例如，某个Actor具有指示该Actor浸在油中的游戏性标记或属性，当它被以火为主题的游戏性效果击中时，它就可以获得"着火"技能，从而被动地烧毁附近的Actor并在接下来的十秒钟之内产生具有粒子和动态光照的视觉效果。
    - 堆叠："堆叠"指的是处理对已具有增益或减益（或者游戏性效果，在本示例中就是如此）的目标再次应用增益或减益，以及处理所谓的"溢出"情况的策略，溢出是指在原Gameplay效果的影响下已完全饱和的目标被应用了新的游戏性效果（例如，不断累积的毒药计时条只有在溢出后才会产生持续伤害效果）。系统支持各种各样的堆叠行为，例如，不断累积直至超出阈值，维护在每次应用后增加直至达到最大限制的"堆叠量"，在限时效果的影响下重置或增补时间，或独立于各个计时器应用该效果的多个实例。
    - 游戏性Cue显示： 游戏性Cue 是可通过游戏性技能系统控制的管理装饰效果（例如，粒子或音效）的方法，它可以节约网络资源。游戏性技能和游戏性效果可以触发它们，它们通过四个可在本地或蓝图代码中覆盖的主函数来产生作用：On Active、While Active、Removed及Executed（仅由游戏性效果使用）。所有游戏性Cue必须与"GameplayCue"开头的游戏性标记相关联，例如"GameplayCue.ElectricalSparks"或"GameplayCue.WaterSplash.Big"。

- 对效果和属性间的交互进行编程
  - 属性集可覆盖多个函数以处理在某个游戏性效果尝试修改属性时它作出反应的方式。例如，样本`USimpleAttributeSet`中的"生命值"属性可以存储浮点值，而且该值可由游戏性技能系统访问或更改，但是当生命值降到零时实际上什么也没有发生，而且也没有什么可以阻止它降到零以下。要使"生命值"属性具有我们想要的行为方式，属性集自身可以进行干预，方法是覆盖多个处理对其任何属性的尝试修改的虚拟函数。以下函数通常会被属性集覆盖：
    - PreAttributeChange / PreAttributeBaseChange：这些函数会在属性被修改前受到调用。它们用于强制实施与属性的值有关的规则，例如"生命值必须介于0和最大生命值之间"，而且不应触发针对属性更改的游戏中反应。
    - PreGameplayEffectExecute：在修改属性的值之前，此函数可拒绝或改变提议的修改。
    - PostGameplayEffectExecute：在修改属性的值之后，此函数可立即对更改作出反应。这通常包括限制属性的最终值，或者触发针对新值的游戏中反应，例如，当"生命值"属性降到零时死去。

## Gameplay Ability System Overview

- Components of the Gameplay Ability System
  - The Gameplay Ability System is designed to address all of these use-cases by modeling abilities as self-contained entities responsible for their own execution. This system consists of several components:
    - An owning Actor with an `Ability System Component`, which maintains a list of all the abilities the Actor owns and handles activation.
    - `Gameplay Ability Blueprints` that represent individual abilities, and coordinate their ingame execution.
      - Composed of `Gameplay Ability Tasks` as well as other functions.
    - An `Attribute Set` attached to the Ability System Component.
      - Contains the `Gameplay Attributes` that drive calculations or represent resources.
    - `Gameplay Effects` that handle changes to Actors as a result of using Abilities.
      - `Gameplay Effect Calculations` that provide modular, reusable methods for calculating effects.
      - `Gameplay Cues` that are associated with Gameplay Effects and provide a data-driven method for handling visual effects.

- Handling Abilities and Their Execution
  - A Gameplay Ability is a Blueprint object that is responsible for executing all of an ability's events, including playing animations, triggering effects, fetching attributes from its owner, and displaying visual effects.

- Supporting Network Multiplayer
  - Ability System Components and Replication
    - To save bandwidth and prevent cheating, Ability System Components do not replicate their full state to all clients. Specifically, they do not replicate Abilities and Gameplay Effects to all clients, only Gameplay Attributes and Tags that they affect.
  - Replicating Abilities and Using Prediction
    - Most abilities in networked games should run on the server and replicate to clients, so there is normally lag in ability activation. This is not desirable in most fast-paced multiplayer games. To mask this lag, you can activate an ability locally, then tell the server you have activated it so that it can catch up.
    - There is a chance that the server rejects the ability activation, which means it must undo the changes the ability made locally. You can handle these cases using locally predicted abilities. To help support this, some Gameplay Effects support rollback if the ability that granted them gets rejected by the server. These include most non-instant GEs, but notably excludes things like damage and other instantaneous attribute/tag changes.
  - Using Abilities to Interact With Server-Owned Objects
    - Gameplay Abilities can handle interactions with bots, NPCs, and other server-owned Actors and objects. You have to do this through a locally owned Actor – usually the player's Pawn – and a replicated ability or another non-GAS mechanism that calls a server function. This replicates the interaction to the server, which then has authority to perform changes with the NPCs.


# GAS Documentation

## 4.1 Ability System Component

- 当你想遍历ActivatableAbility.Items时, 确保在循环体之上添加ABILITYLIST_SCOPE_LOCK();来锁定列表以防其改变(比如移除一个Ability)

## 4.2 Gameplay Tags

- 如果GameplayTag由GameplayEffect添加, 那么其就是可同步的. ASC允许你添加不可同步的LooseGameplayTag且必须手动管理. 样例项目对State.Dead使用了LooseGameplayTag, 因此当生命值降为0时, 其所属客户端会立即响应. 重生时需要手动将TagMapCount设置回0, 当使用LooseGameplayTag时只能手动调整TagMapCount, 相比纯手动调整TagMapCount, 最好使用UAbilitySystemComponent::AddLooseGameplayTag()和UAbilitySystemComponent::RemoveLooseGameplayTag()

## 4.3 Attribute

- 一些Attribute被视为占位符, 其是用于预计和Attribute交互的临时值, 这些Attribute被叫做Meta Attribute. Meta Attribute对于在"我们应该造成多少伤害?"和"我们该如何处理伤害值?"这种问题之中的伤害值和治疗值做了很好的解构, 这种解构意味着GameplayEffect和ExecutionCalculation无需了解目标是如何处理伤害值的

## 4.4 AttributeSet

- Attribute添加到GetLifetimeReplicatedProps中应使用REPTNOTIFY_Always，是用于设置OnRep函数在客户端值已经与服务端同步的值相同的情况下触发(因为有预测), 默认设置下, 客户端值与服务端同步的值相同时, OnRep函数是不会触发的

## 4.5 Gameplay Effects

- 在Gameplay Effect Modifiers中，预测(Prediction)对于百分比修改有些问题
- 每个Modifier都可以设置SourceTag和TargetTag, 它们的作用就像GameplayEffect的Application Tag requirements, 因此只有当Effect应用后才会考虑标签, 对于周期性(Periodic)的无限(Infinite)Effect, 这些标签只会在第一次应用Effect时才会被考虑, 而不是在每次周期执行时
- ExecutionCalculation只能由即刻(Instant)和周期性(Periodic)GameplayEffect使用, 对于Local Predicted, Server Only和Server Initiated的GameplayAbility, ExecCalc只在服务端调用
  - 发送数据到Execution Calculation的几种方式
    1. SetByCaller
    1. Backing Data Attribute Calculation Modifier
    1. Backing Data Temporary Variable Calculation Modifier(添加Backing临时变量到ExecutionCalculation的构造函数: ValidTransientAggregatorIdentifiers.AddTag(FGameplayTag::RequestGameplayTag("Data.Damage"));)
    1. GameplayEffectContext
- 当GameplayEffectSpec创建时, Snapshot会捕获Attribute, 而当GameplayEffectSpec应用时, 非Snapshot会捕获Attribute. 捕获Attribute会自ASC现有的Modifier重新计算它们的CurrentValue, 该重新计算不会执行AbilitySet中的PreAttributeChange(), 因此所有的限制操作(Clamp)必须在这里重新处理
- CustomApplicationRequirement(CAR)类为设计师提供对于GameplayEffect是否可以应用的高阶控制, 而不是对GameplayEffect进行简单的GameplayTag检查. 这可以通过在蓝图中重写CanApplyGameplayEffect()和在C++中重写CanApplyGameplayEffect_Implementation()实现.

## 4.6 Gameplay Abilities

- 传递数据到Ability的方式
  - Activate GameplayAbility by Event
  - Use WaitGameplayEvent AbilityTask(该方法的缺点是Event不能通过AbilityTask同步且只能用于Local Only和Server Only的GameplayAbility. 你可以编写自己的AbilityTask以支持同步Event负载(Payload))
  - Use TargetData
  - Store Data on the OwnerActor or AvatarActor(这种方法最灵活且可以用于由输入绑定激活的GameplayAbility, 然而, 它不能保证在使用时数据同步)
- Ability Batching
  - 一般GameplayAbility的生命周期最少涉及2到3个自客户端到服务端的RPC
  - 如果GameplayAbility在一帧同一原子(Atomic)组中执行这些操作, 我们就可以优化该工作流, 将所有2个或3个RPC批处理(整合)为1个RPC
- GameplayAbility的网络安全策略(Net Security Policy)决定了Ability应该在网络的何处执行. 它为尝试执行限制Ability的客户端提供了保护.

## 4.7 Ability Tasks

- UAbilityTask的构造函数中强制硬编码允许最多1000个同时运行的AbilityTask, 当设计那些同时拥有数百个Character的游戏(像RTS)的GameplayAbility时要注意这一点.
- 在蓝图中, 我们只需使用为AbilityTask创建的蓝图节点, 不必调用ReadyForActivate(), 其由Engine/Source/Editor/GameplayTasksEditor/Private/K2Node_LatentGameplayTaskCall.cpp自动调用, K2Node_LatentGameplayTaskCall也会自动调用BeginSpawningActor()和FinishSpawningActor()
- 强调一遍, K2Node_LatentGameplayTaskCall只会对蓝图做这些自动操作, 在C++中, 我们必须手动调用ReadyForActivation(), BeginSpawningActor()和FinishSpawningActor()
- Root Motion Source Ability Task
  - GAS自带的AbilityTask可以使用挂载在CharacterMovementComponent中的Root Motion Source随时间推移而移动Character, 像击退, 复杂跳跃, 吸引和猛冲

## 4.8 Gameplay Cues

- GameplayCue(GC)执行非游戏逻辑相关的功能, 像音效, 粒子效果, 镜头抖动等等. GameplayCue一般是可同步(除非在客户端明确执行(Executed), 添加(Added)和移除(Removed))和可预测的
- 从GameplayAbility和ASC中暴露的用于触发GameplayCue的函数默认是可同步的. 每个GameplayCue事件都是一个多播(Multicast)RPC. 这会导致大量RPC. GAS也强制在每次网络更新中最多能有两个相同的GameplayCueRPC. 我们可以通过使用客户端GameplayCue来避免这个问题. 客户端GameplayCue只能在单独的客户端上Execute, Add或Remove
- 默认情况下, 游戏开始时GameplayCueManager会扫描游戏的全部目录以寻找GameplayCueNotify并将其加载进内存, 在启动时异步加载每个GameplayCue的一种可选方法是只异步加载那些会在游戏中触发的GameplayCue, 这会在异步加载每个GameplayCue时减少不必要的内存占用和潜在的游戏无响应几率, 从而避免特定GameplayCue在游戏中第一次触发时可能出现的延迟效果

- 手动RPC: 每次GameplayCue触发都是一次不可靠的多播(NetMulticast)RPC. 在同一时刻触发多个GameplayCue的情况下, 有一些优化方法来将它们压缩成一个RPC或者通过发送更少的数据来节省带宽
  - 假设你有一个可以发射8枚弹丸的霰弹枪, 就会有8个轨迹和碰撞GameplayCue. GASShooter采用将它们联合成一个RPC的延迟(Lazy)方法, 其将所有的轨迹信息保存到EffectContext作为TargetData
  - 尽管其将RPC数量从8降为1, 然而还是在这一个RPC中通过网络发送大量数据(~500 bytes). 一个进一步优化的方法是使用一个自定义结构体发送RPC, 在该自定义RPC中你需要高效编码命中位置(Hit Location)或者给一个随机种子以在接收端重现/近似计算碰撞位置, 客户端之后需要解包该自定义结构体并重现客户端执行的GameplayCue
- GameplayEffect中的多个GameplayCue:
  - 默认情况下, UGameplayCueManager::InvokeGameplayCueAddedAndWhileActive_FromSpec()会在不可靠的多播(NetMulticast)RPC中发送整个GameplayEffectSpec(除了转换为FGameplayEffectSpecForRPC)而不管ASC的同步模式, 取决于GameplayEffectSpec的内容, 这可能会使用大量带宽, 我们可以通过设置AbilitySystem.AlwaysConvertGESpecToGCParams 1来将其优化, 这会将GameplayEffectSpec转换为FGameplayCueParameter结构体并且RPC它而不是整个FGameplayEffectSpecForRPC, 这会节省带宽但是只有较少的信息
