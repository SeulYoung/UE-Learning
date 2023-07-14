# Gameplay框架

## Actors

- Actor不直接保存变换（位置、旋转和缩放）数据；如Actor的根组件存在，则使用它的变换数据。

- 在某种意义上，Actor 可被视为包含特殊类型 对象（称作组件）的容器。 不同类型的组件可用于控制Actor移动的方式及其被渲染的方式，等等。Actor的其他主要功能是在游戏进程中在网络上进行属性复制 和函数调用。
  - 组件的主要类型有：
    - UActorComponent：这是基础组件。其可作为Actor的一部分被包含。如果需要，其可进行Tick。ActorComponents与特定的Actor相关联，但不存在于场景中的任意特定位置。它们通常用于概念上的功能，如AI或解译玩家输入。
    - USceneComponent：SceneComponents是拥有变换的ActorComponents。变换是场景中的位置，由位置、旋转和缩放定义。SceneComponents能以层级的方式相互附加。Actor的位置、旋转和缩放取自位于层级根部的SceneComponent。
    - UPrimitiveComponent：PrimitiveComponent是拥有一类图像表达（如网格体或粒子系统）的SceneComponent。诸多有趣的物理和碰撞设置均在此处。
  - Actor支持拥有一个SceneComponent的层级。每个Actor也拥有一个 RootComponent 属性，将指定作为Actor根的组件。Actor自身不含变换，因此不带位置、旋转，或缩放。 它们依赖于其组件的变换，具体来说是其根组件的变换。如果此组件是一个 SceneComponent，其将提供Actor的变换信息。 否则Actor将不带变换。其他附加的组件拥有相对于其附加到的组件的变换。

- 销毁Actor
  - Actor通常不会被垃圾回收，因为场景对象保存一个Actor引用的列表。调用 Destroy() 即可显式销毁Actor。 这会将其从关卡中移除，并将其标记为"待销毁"，这说明其在下次垃圾回收中被清理之前都将存在。

### Actor通信

- 使用蓝图类引用表进行通信
  - 直接通信：在与关卡中Actor的特定实例通信时。需要引用关卡中的Actor。例如在关卡中的特定Actor上触发事件。
  - 类型转换：希望验证Actor是否属于特定类，以便访问其属性。需要引用关卡中的Actor以类型转换到所需的Actor类。例如访问属于同一父类的子Actor的特定功能。
  - 接口：当你需要为不同Actor添加相同功能时。需要引用关卡中的Actor，并且该Actor需要实现接口。例如为不同类型的Actor添加交互行为。
  - 事件分发器：通过一个Actor来触发到多个Actor的事件。Actor需要订阅事件，以便对事件作出响应。例如通知不同类型的Actor：某事件已经触发。

### Actor 生命周期

- 生命周期详解
  ![生命周期详解](https://docs.unrealengine.com/5.2/Images/making-interactive-experiences/interactive-framework/actors/actor-lifecycle/ActorLifeCycle1.png)
  - 从磁盘加载
    - 已位于关卡中的 Actor 使用此路径，如 LoadMap 发生时、或 AddToWorld（从流关卡或子关卡）被调用时。
  - Play in Editor
    - Play in Editor 路径与 Load from Disk 十分相似，然而 Actor 却并非从磁盘中加载，而是从编辑器中复制而来。
  - 延迟生成
    - 将任意属性设为"Expose on Spawn"即可延迟 Actor 的生成。

- 生命走向终点
  - 销毁 Actor 的方式有许多种，但终结其存在的方式始终如一。
  - 在游戏Gameplay期间
    - Destroy - 游戏在 Actor 需要被移除时手动调用，但游戏进程仍在继续。Actor 被标记为等待销毁并从关卡的 Actor 阵列中移除。
    - EndPlay - 在数个地方调用，保证 Actor 的生命走向终点。在游戏过程中，如包含流关卡的 Actor 被卸载，Destroy 将发射此项和关卡过渡。调用 EndPlay 的全部情形：
      - Explicit call to Destroy.
      - Play in Editor Ended.
      - Level Transition (seamless travel or load map).
      - A streaming level containing the Actor is unloaded.
      - The lifetime of the Actor has expired.
      - Application shut down (All Actors are Destroyed).
    - 无论这些情形出现的方式如何，Actor 都将被标记为 RF_PendingKill，因此在下个垃圾回收周期中它将被解除分配。此外，可以考虑使用更整洁的 `FWeakObjectPtr<AActor>` 代替手动检查"等待销毁"。
  - 垃圾回收：一个对象被标记待销毁的一段时间后，垃圾回收会将其从内存中实际移除，释放其使用的资源。
    - 在对象的销毁过程中，以下函数将被调用：
      - BeginDestroy - 对象可利用此机会释放内存并处理其他多线程资源（即为图像线程代理对象）。与销毁相关的大多数游戏性功能理应在 EndPlay 中更早地被处理。
      - IsReadyForFinishDestroy - 垃圾回收过程将调用此函数，以确定对象是否可被永久解除分配。返回 false，此函数即可延迟对象的实际销毁，直到下一个垃圾回收过程。
      - FinishDestroy - 最后对象将被销毁，这是释放内部数据结构的另一个机会。这是内存释放前的最后一次调用。

### Actor Ticking

- Ticking
  - 正确理解游戏 actor 和组件之间相对的 tick 顺序和 引擎执行的其他每帧任务十分重要，可避免帧差一问题，并确保游戏运行的一致性。Actors 和组件可设为每帧 tick，也可设为以最低时间间隔 tick，或完全不 tick。此外，它们可在引擎每帧更新循环中的不同阶段被合并为组；也可接受单独指令，等待特定 tick 完成后再开始。

- Tick 组
  - 除非已指定最低 tick 间隔，否则 Actors 和组件每帧 tick 一次。Ticking 根据 tick 组发生。Tick 组可在代码或蓝图中指定。Actor 或组件的 tick 组用于确定在帧中何时进行 tick，相对于其他引擎中的帧处理（主要是物理模拟）。
  - 每个 tick 组将完成对指定的每个 actor 和组件的 tick，然后再开始下一个 tick 组。除 tick 组外，actors 或组件还可设置 tick 依赖性，意味着其他特定 actor 或组件的 tick 函数完成后它们才会进行 tick。Tick 组和 tick 依赖性的使用十分重要，可确保游戏在涉及到多个 actors 或组件的物理相依行为或循序游戏性行为方面工作正常。

- Tick 组排序
  - TG_PrePhysics
    - Actor 将与物理对象（包括基于物理的附着物）进行交互时使用的 tick 组。如此，actor 的运动便完成，并可被纳入物理模拟因素。
    - 此 tick 中的物理模拟数据属于上一帧 — 也就是上一帧渲染到屏幕上的数据。
  - TG_DuringPhysics
    - 因它在物理模拟的同时运行，无法确定此 tick 中的物理数据来自上一帧或当前帧。物理模拟可在此 tick 组中的任意时候完成，且不会显示信息来表达此结果。
    - 因为物理模拟数据可能来自当前帧或上一帧，此 tick 组只推荐用于无视物理数据或允许一帧偏差的逻辑。常见用途为更新物品栏画面或小地图显示。此处物理数据完全无关，或显示要求不精确，一帧延迟不会造成问题。
  - TG_PostPhysics
    - 此 tick 组运行时，此帧的物理模拟结果已完成。
    - 此组可用于武器或运动追踪。渲染此帧时所有物理对象将位于它们的最终位置。这尤其适用于射击游戏中的激光瞄准器。在此情况中激光束必须从枪的最终位置发出，即便出现一帧延迟也会十分明显。
  - TG_PostUpdateWork
    - 这在 TG_PostPhysics 之后运行。从以往来看，它的基函数是将最靠后的信息送入粒子系统。
    - 在摄像机更新后发生。如特效必须知晓摄像机朝向的准确位置，可将控制这些特效的 actor 放置于此。
    - 这也可用于在帧中绝对最靠后运行的游戏逻辑，如解决格斗游戏中两个角色在同一帧中尝试抓住对方的情况。

- Tick 依赖性
  - 存在于 actor 和组件上的 AddTickPrerequisiteActor 和 AddTickPrerequisiteComponent 函数将设置存在函数调用的 actor 或组件等待 tick，直到特定的其他 actor 或组件完成 tick。
  - 这尤其适用于这样的情况：在帧中几乎相同时间发生，但一个 actor/组件将设置另一个 actor/组件所需的数据。在 tick 组上使用它的原因是：如存在于相同组中，许多 actor 可被并行更新。如 actors 只是个体依赖于一个或两个其他 actors，而无需等待整个组完成后再进行 tick，则没有必要将一组 actors 移动到一个全新的组。

- Actor 生成
  - 在 BeginPlay 中，actor 将向引擎注册其主 tick 函数和其组件的 tick 函数。Actor 的 tick 函数可通过 PrimaryActorTick 成员设为在特定 tick 组中运行，或完全禁用。这通常在构造函数中完成，以确保 BeginPlay 调用前数据设置正确。

- 组件 Tick
  - 组件可以和 Actor 一样被分隔为不同的 tick 组。之前，Actor 在 Actor 的 tick 中 tick 其所有组件。这仍在发生，但需要处于不同群组中的组件将被添加到一个列表中，在这些组件被 tick 时进行管理。将组件指定到 tick 组时应使用指定 actor 到 tick 组的相同标准。组件的 tick 结构的命名方式与 Actor 有所不同，但工作方式相同

- 高级 Tick 功能
  - Actor 或组件的默认 tick 函数可在游戏中分别通过 AActor::SetActorTickEnabled 和 UActorComponent::SetComponentTickEnabled 函数启用或禁用。此外，一个 actor 或组件可拥有多个 tick 函数。达成方法为：创建一个继承自 FTickFunction 的结构体，并覆写 ExecuteTick 和 DiagnosticMessage 函数。默认 actor 和组件 tick 函数结构是自行构建的好参考，可在 FActorTickFunction 和 FComponentTickFunction 下的 EngineBaseTypes.h 中找到它们。
  - 将自建的 tick 函数结构添加到 actor 或组件后即可将其初始化（通常在拥有类的构造函数中进行）。启用和注册 tick 函数的最常用路径是覆写 AActor::RegisterActorTickFunctions 并添加调用到 tick 函数结构的 SetTickFunctionEnable，之后是作为参数的 RegisterTickFunction （含拥有 actor 的等级）。此过程的最终结果是：创建的 actor 或组件可进行多次 tick，包括不同组中的 tick，以及每个 tick 函数单独的依赖性。手动设置 tick 依赖性的方法为：在需要依赖于其他函数结构的 tick 函数结构上调用 AddPrerequisite，然后传入用作依赖性的 tick 函数结构。

## 摄像机



## 组件

- 组件 是一种特殊类型的 对象，Actor 可以将组件作为子对象附加到自身。组件适用于共享相同的行为，例如显示视觉表现、播放声音。它们还可以表示项目特有的概念，例如载具解译输入和改变其速度与方向的方式。

- Actor Components
  - UActorComponent 是所有组件的基类。由于组件是渲染网格体和图像、实现碰撞和播放音频的唯一方法，因此玩家游戏期间在场景中看到或进行交互的一切其实都是某一类组件的成果。
  - 创建自己的组件时，需要了解一些主要的类：Actor组件、场景组件 和 Primitive组件。
    - Actor组件（类 UActorComponent）最适用于抽象行为，例如移动、物品栏或属性管理，以及其他非物理概念。Actor组件没有变换，即它们在场景中不存在任何物理位置或旋转。
    - 场景组件（类 USceneComponent，其是UActorComponent 的子项）支持基于位置的行为，这类行为不需要几何表示。这包括弹簧臂、摄像机、物理力和约束（但不包括物理对象），甚至音频。
    - Primitive组件（类 UPrimitiveComponent，其是USceneComponent 的子项）是拥有几何表示的场景组件，通常用于渲染视觉元素或与物理对象发生碰撞或重叠。这包括静态或骨架网格体、Sprite或公告板、粒子系统以及盒体、胶囊体和球体碰撞体积。

- 注册组件
  - 为了让Actor组件能够逐帧更新并影响场景，引擎必须 注册 这类组件。如果在Actor产生过程中，作为Actor子对象自动创建了组件，则这类组件会自动注册。但是，游戏期间创建的组件可以使用手动注册。RegisterComponent 函数提供了这个功能，要求是组件与Actor关联。
    - 游戏期间注册组件可能会影响性能，因此只应在必要时进行此操作。
  - 注册事件
    - 在注册组件的过程中，引擎会将组件与场景关联起来，让其可用于逐帧更新，并运行以下 UActorComponent 函数：OnRegister、CreateRenderState、OnCreatePhysicsState

- 取消注册组件
  - 要从更新、模拟或渲染过程中移除Actor组件，可以使用 UnregisterComponent 函数将其取消注册。
  - 取消注册事件
    - 在组件取消注册时，将运行下面的 UActorComponent 函数：OnUnregister、DestroyRenderState、OnDestroyPhysicsState

- 更新
  - Actor组件能够以类似于Actor的方法逐帧更新。TickComponent 函数允许组件逐帧运行代码。
  - 默认情况下，Actor组件不更新。为了让Actor组件逐帧更新，必须在构造函数中将 PrimaryComponentTick.bCanEverTick 设置为 true 来启用tick。之后，在构造函数中或其他位置处，必须调用 PrimaryComponentTick.SetTickFunctionEnable(true) 以开启更新。之后可调用 PrimaryComponentTick.SetTickFunctionEnable(false) 停用tick。
    - 如果您知道组件永远不需要更新，或者打算手动调用自己的更新函数（也许从拥有的Actor类），将 PrimaryComponentTick.bCanEverTick 保留为默认值 false 即可，这样可以稍微改善性能。

- 渲染状态
  - 为进行渲染，Actor组件必须创建渲染状态。此渲染状态还会告诉引擎，需要更新渲染数据的组件已发生变更。当发生此类变更时，渲染状态会被标记为"dirty"。如果编译您自己的组件，可以使用 MarkRenderStateDirty 函数将渲染数据标记为dirty。在一帧结束时，所有dirty组件的渲染数据都会在引擎中更新。场景组件（包括Primitive组件）默认会创建渲染状态，而Actor组件则不会。

- 物理状态
  - 要与引擎的物理模拟系统交互，Actor组件需要物理状态。物理状态会在发生变化时立即更新，防止出现"帧落后"瑕疵等问题，也不需要"dirty"标记。默认情况下，Actor组件和场景组件没有物理状态，但Primitive组件有。覆盖 ShouldCreatePhysicsState 函数以确定组件类实例是否需要物理状态。
  - 如果类使用物理，则不建议只返回 true。请参阅函数的 UPrimitiveComponent 版本，了解不应创建物理状态的情况（例如在组件破坏期间）。可以返回 Super::ShouldCreatePhysicsState以替换在正常返回 true 的情况下。

- 视觉化组件
  - 某些Actor和组件没有视觉表示，使它们难以选择，或有一些重要属性不可见。在编辑器中工作时，开发者可以添加额外的组件来显示信息，但在编辑器中运行时或运行打包版本时不需要这些额外组件。为解决这个问题，编辑器支持 视觉化组件 的概念，这是只在编辑器中工作时存在的普通组件。
  - 要创建视觉化组件，需创建常规组件并在其上方调用 SetIsVisualizationComponent。由于组件无需存在于编辑器之外，所有对它的引用都应当处在对 WITH_EDITORONLY_DATA 或 WITH_EDITOR 的预处理器检查之中。这将确保打包版本不受这些组件的影响，并保证不会在代码中的任何位置引用它们。

- Scene Components
  - 场景组件是指存在于场景中特定物理位置处的Actor组件。该位置由 变换（类 FTransform）定义，其中包含组件的位置、旋转和缩放。场景组件能够通过将彼此连接起来形成树结构，Actor可以将单个场景组件指定为"根"，意味着这个Actor的场景位置、旋转和缩放都根据此组件来绘制。
  - 附加
    - 只有场景组件（USceneComponent 及其子类）可以彼此附加，因为需要变换来描述子项和父项组件之间的空间关系。虽然场景组件可以拥有任意数量的子项，但只能拥有一个父项，或可直接放置在场景中。场景组件系统不支持附加循环。
    - 两种主要方法分别是 SetupAttachment 和 AttachToComponent。前者在构造函数中、以及处理尚未注册的组件时十分实用；后者会立即将场景组件附加到另一个组件，在游戏进行中十分实用。
    - 该附加系统还允许将Actor彼此之间进行附加，方法是将一个Actor的根组件附加到属于另一个Actor的组件。

- Primitive Components
  - 基元组件（类 UPrimitiveComponent）是包含或生成某类几何的场景组件，通常用于渲染或碰撞。各种类型的几何体，目前最常用的是 盒体组件、胶囊体组件、静态网格体组件 和 骨架网格体组件。盒体组件和胶囊体组件生成不可见的几何体进行碰撞检测，而静态网格体组件和骨架网格体组件包含将被渲染的预制几何体，需要时也可以用于碰撞检测。
  - 场景代理
    - 基元组件的 场景代理（类 FPrimitiveSceneProxy）封装场景数据，引擎使用这些数据来与游戏线程并行渲染组件。每种类型的基元都有自身的场景代理子类，用来保存所需的特定渲染数据。

### 移动组件

- 人物移动组件
  - 角色移动组件（CharacterMovementComponent） 允许非物理刚体类的角色移动（走、跑、跳、飞、跌落和游泳）。 该组件专用于 角色（Characters），无法由其他类实现。当你创建一个继承自 Characters 的 蓝图（Blueprints） 时，CharacterMovementComponent会自动添加，无需你手动添加。
  - 组件包含一些可设置属性，包括角色跌落和行走时的摩擦力、角色飞行、游泳、以及行走时的速度、浮力、重力系数、以及人物可施加在物理对象上的力。 CharacterMovementComponent还包含动画自带的、且已经转换成世界空间的根骨骼运动参数，可供物理系统使用。

- 发射物移动组件
  - 在更新（Tick）过程中，发射物移动组件（ProjectileMovementComponent） 会更新另一个组件的位置。该组件还支持碰撞后的跳弹以及跟踪等功能。 通常情况下，拥有该组件的Actor的根组件会发生移动；不过，可能会选择另一个组件（see SetUpdatedComponent). 如果更新后的组件正在进行物理模拟，只有初始参数（当初始速度非零时）将影响子弹（Projectile），且物理模拟将从该位置开始。

- 旋转移动组件
  - RotatingMovementComponent 允许某个组件以指定的速率执持续旋转。（可选）你可以偏移旋转时参照的枢轴点。注意，在移动过程中，无法进行碰撞检测。
  - 使用旋转移动组件的案例包括：飞机螺旋桨、风车，甚至是围绕恒星旋转的行星。

## 游戏功能和模块化Gameplay

- 游戏功能（Game Features） 和 模块化Gameplay（Modular Gameplay） 插件可以帮助开发人员为项目创建独立功能。使用插件来构建功能有多种优势：
  - 保持你的项目代码库的清洁且可读。
  - 避免不相关的功能之间意外交互或依赖。在开发那些需要经常改动功能的已上线产品时，这尤为重要。

## Game Mode 和 Game State

- 即使最开放的游戏也拥有基础规则，而这些规则构成了 Game Mode。
- 基于规则的事件在游戏中发生，需要进行追踪并和所有玩家共享时，信息将通过 Game State 进行存储和同步。

- AGameModeBase
  - 所有 Game Mode 均为 AGameModeBase 的子类。而 AGameModeBase 包含大量可覆盖的基础功能。
    - 部分常见函数包括：InitGame、PreLogin、PostLogin、HandleStartingNewPlayer、RestartPlayer、SpawnDefaultPawnAtTransform、Logout
  - 可针对游戏提供的每个比赛格式、任务类型或特殊区域创建 AGameModeBase 的子类。一款游戏可拥有任意数量的 Game Mode，因此也可拥有任意数量的 AGameModeBase 类子类；然而，给定时间上只能使用一个 Game Mode。每次关卡进行游戏实例化时 Game Mode Actor 将通过 UGameEngine::LoadMap() 函数进行实例化。
  - Game Mode 不会复制到加入多人游戏的远程客户端；它只存在于服务器上，因此本地客户端可看到之前使用过的留存 Game Mode 类（或蓝图）；但无法访问实际的实例并检查其变量，确定游戏进程中已发生哪些变化。如玩家确实需要更新与当前 Game Mode 相关的信息，可将信息保存在一个 AGameStateBase Actor 上，轻松保持同步。AGameStateBase Actor 随 Game Mode 而创建，之后被复制到所有远程客户端。

- AGameMode
  - AGameMode 是 AGameModeBase 的子类，拥有一些额外的功能支持多人游戏和旧行为。所有新建项目默认使用 AGameModeBase。如果需要此额外行为，可切换到从 AGameMode 进行继承。如从 AGameMode 进行继承，也可从 AGameState 继承游戏状态（其支持比赛状态机）。
  - AGameMode 包含一个跟踪比赛状态或整体游戏流程的状态机。可使用 GetMatchState 或 HasMatchStarted、IsMatchInProgress 和 HasMatchEnded 之类的封装器查询当前的状态。
  - 游戏状态将固定为 InProgress，因为这是调用 BeginPlay、actor 开始 tick 的状态。然而，个体游戏可能覆盖这些状态的行为，用更复杂的规则构建一个多人游戏，如在一款多人射击游戏中等待其他玩家加入时允许玩家在关卡中自由飞行。

- Game Mode 蓝图
  - 可创建派生自 Game Mode 类的蓝图，并将它们用作项目或关卡的默认 Game Mode。
  - Game Mode 的蓝图十分实用，因为它们无需调整代码即可启用变量调整。因此可用于使单一 Game Mode 适用到多个不同关卡，无需使用硬编码资源引用或为每次调整请求工程支持和代码修改。

- 设置 Game Mode
  - 设置关卡的 Game Mode 有多种，此处的排序从优先级最低到最高：
    - 设置 DefaultEngine.ini 文件的 /Script/EngineSettings.GameMapsSettings 部分的 GlobalDefaultGameMode 输入将设置项目中所有地图的默认游戏模式。
    - 在编辑器中 World Settings 标签下设置 GameMode Override 即可覆盖个体地图的项目设置。
    - URL 可被传到可执行文件，强制游戏加载时 带特定选项。使用 game 选项设置游戏模式。
    - 最后，可在 DefaultEngine.ini 文件的 /Script/Engine.WorldSettings/ 部分中设置地图前缀（和 URL 法的别名）。这些前缀设置所有拥有特定前缀的地图的默认游戏模式。

- Game State
  - Game State 负责启用客户端监控游戏状态。从概念上而言，Game State 应该管理所有已连接客户端已知的信息（特定于 Game Mode 但不特定于任何个体玩家）。它能够追踪游戏层面的属性，如已连接玩家的列表、夺旗游戏中的团队得分、开放世界游戏中已完成的任务，等等。
  - Game State 并非追踪玩家特有内容（如夺旗比赛中特定玩家为团队获得的分数）的最佳之处，因为它们由 Player State 更清晰地处理。整体而言，GameState 应该追踪游戏进程中变化的属性。这些属性与所有人皆相关，且所有人可见。Game mode 只存在于服务器上，而 Game State 存在于服务器上且会被复制到所有客户端，保持所有已连接机器的游戏进程更新。

## Pawn

- Pawn 是可那些由玩家或 AI 控制的所有 Actor 的基类。Pawn 是玩家或 AI 实体在游戏场景中的具化体现。Character 是一种特殊的、可以行走的 Pawn。
  - 默认情况下，控制器（Controllers）和 Pawn 之间是一对一的关系；也就是说，每个控制器在某个时间点只能控制一个 Pawn。此外，在游戏期间生成的 Pawn 不会被控制器自动控制。

## Characters

- 添加 CharacterMovementComponent、CapsuleComponent 和 SkeletalMeshComponent 后，Pawn 类可延展为功能完善的 角色 类。 角色用于代表垂直站立的玩家，可以在场景中行走、跑动、跳跃、飞行和游泳。 此类也包含基础网络连接和输入模型的实现。
  - SkeletalMeshComponent：与pawn不同的是，角色自带 SkeletalMeshComponent，可启用使用骨架的高级动画。可以将其他骨架网格体添加到角色派生的类，但这才是与角色相关的主骨架网格体。
  - CapsuleComponent：CapsuleComponent 用于运动碰撞。为了计算 CharacterMovementComponent 的复杂几何体，会假设角色类中的碰撞组件是垂直向的胶囊体。
  - CharacterMovementComponent：CharacterMovementComponent 能够使人身不使用刚体物理即可行走、跑动、飞行、坠落和游泳。 其为角色特定，无法被任何其他类实现。 可在 CharacterMovementComponent 中设置的属性包含了摔倒和行走摩擦力的值、在空气、水、土地中行进的速度、浮力、重力标度，以及角色能对物理对象施加的物理力。 CharacterMovementComponent 还包含来自动画的根运动参数， 其已转换到世界空间中，可直接用于物理。

## Gameplay框架快速参考

- 框架类关系
  - 此流程图说明了这些Gameplay类是如何相互关联的。游戏由游戏模式和游戏状态组成。加入游戏的人类玩家与玩家控制器相关联。 这些玩家控制器允许玩家在游戏中拥有Pawn，这样他们就可以在关卡中拥有物理代表。玩家控制器还向玩家提供输入控制、抬头显示（HUD）， 以及用于处理摄像机视图的玩家摄像机管理器。
  ![框架类关系](https://docs.unrealengine.com/5.2/Images/making-interactive-experiences/interactive-framework/QuickReference/GameFramework.webp)

## Gameplay定时器

- 定时器管理
  - 定时器在全局 定时器管理器（FTimerManager类型）中管理。全局定时器管理器存在于 **游戏实例** 对象上以及每个 **场景** 中。有两个函数可以使用定时器管理器来设置定时器：SetTimer和SetTimerForNextTick，它们各自都有一些重载。每个函数都可以连接到任意类型的对象或函数委托，SetTimer可以设为根据需要定期重复。
  - 要访问定时器管理器，可以使用`AActor`函数`GetWorldTimerManager`，它会在`UWorld`中调用`GetTimerManager`函数。
  - 要访问全局定时器管理器，使用`UGameInstance`函数`GetTimerManager'。如果场景因为任何原因而没有自己的定时器管理器，也可以退而求其次，使用全局定时器管理器。全局管理器可以用于与任何特定场景的存在没有相关性或依赖性的函数调用。

- 设置和清空定时器
  - FTimerManager 的 SetTimer 函数将定时器设置为在一段延迟后调用函数或委托，可以设置为不限次重复调用该函数。这些函数将填充 定时器句柄（`FTimerHandle`类型），后者可用于暂停（和恢复）倒计时，查询或更改剩余时间，甚至可以取消定时器。
  - 要清空定时器，将 SetTimer 期间填充的 FTimerHandle 传递到 FTimerManager 函数 ClearTimer 中。定时器句柄将在此刻失效，并可以再次用于管理新定时器。
  - 最后，与特定对象关联的所有定时器都可以通过调用`ClearAllTimersForObject`来清空。

- 暂停和恢复定时器
  - `FTimerManager`函数`PauseTimer`使用定时器句柄来暂停正在运行的定时器。这样可阻止定时器执行其函数调用，但经过的时间和剩余时间将保持暂停时的状态。`UnPauseTimer`使暂停的定时器恢复运行。
