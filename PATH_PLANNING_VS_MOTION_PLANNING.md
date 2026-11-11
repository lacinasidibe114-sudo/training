En robotique, la différence entre **path planning** (planification de chemin) et **motion planning** (planification de mouvement) est une question de **niveau d’abstraction** et de **ce que l’on cherche à produire**.

## 1. Path planning — Planification de chemin

**Objectif :** trouver *où* passer pour aller d’un point A à un point B, sans collision.

- **Entrées :** carte, position de départ, objectif, obstacles statiques.
- **Sortie :** un **chemin** — une suite de poses ou de waypoints `(x, y, θ)`.
- **Notion de temps :** souvent ignorée. On ne dit pas à quelle vitesse ni quand le robot passe.
- **Contraintes typiques :** géométrie, obstacles, espace libre.
- **Algorithmes classiques :** A*, Dijkstra, RRT, PRM, Hybrid-A*, State Lattice.
- **Dans ROS 2 / Nav2 :** c’est le rôle du **planner global** (`planner_server`), par exemple `NavFn`, `SmacPlannerHybrid`. Il publie un `/plan`.

**Analogie :** c’est l’itinéraire sur une carte. « Passe par ce couloir, puis tourne à droite. »

## 2. Motion planning — Planification de mouvement

**Objectif :** trouver *comment* le robot doit se déplacer pour suivre ou atteindre un objectif, en respectant sa cinématique, sa dynamique et le temps.

- **Entrées :** chemin ou objectif, modèle du robot, vitesses, accélérations, contraintes d’actionneurs, obstacles dynamiques.
- **Sortie :** une **trajectoire** (chemin + profil temporel) ou directement des **commandes** (`cmd_vel`).
- **Notion de temps :** essentielle. On raisonne en vitesse, accélération, braquage, etc.
- **Contraintes typiques :** rayon de braquage, vitesses maximales, dynamique, collisions futures.
- **Algorithmes classiques :** DWA, MPPI, TEB, CHOMP, OMPL, MoveIt.
- **Dans ROS 2 / Nav2 :** c’est le rôle du **contrôleur / planificateur local** (`controller_server`), par exemple MPPI, DWA, RPP. Il publie `/cmd_vel`.

**Analogie :** c’est la façon de conduire. « Accélère doucement, freine ici, tourne le volant de tant, évite le piéton. »

## 3. Différence clé en une phrase

- **Path planning** : *où* aller — problème surtout **géométrique et spatial**.
- **Motion planning** : *comment* y aller — problème **spatio-temporel, cinématique et dynamique**.

Le **motion planning** est donc plus général : il inclut souvent le path planning comme sous-problème, puis ajoute la dimension temporelle, les vitesses, la dynamique et parfois le contrôle.

## 4. Tableau comparatif

| Critère | Path planning | Motion planning |
|---|---|---|
| Question | Où passer ? | Comment se déplacer ? |
| Sortie | Chemin / waypoints | Trajectoire / commandes |
| Temps | Souvent ignoré | Pris en compte |
| Contraintes | Obstacles, géométrie | Cinématique, dynamique, actionneurs |
| Algorithmes | A*, Dijkstra, RRT, Smac | DWA, MPPI, TEB, CHOMP |
| Nav2 | Planner global | Contrôleur / planner local |

## 5. Nuance importante

Dans certains contextes, notamment en **robotique manipulateur**, le terme *motion planning* est souvent utilisé pour ce que les roboticiennes et roboticens mobiles appellent *path planning* : trouver un chemin dans l’espace des configurations. Mais si l’on parle de **ROS 2 / Nav2** et de **robotique mobile**, la distinction la plus utile est :

- **path planning = planification globale du chemin** ;
- **motion planning = planification locale / trajectoire / contrôle du mouvement**.

En résumé : **le path planning dit où passer ; le motion planning dit comment y aller en respectant le robot et le temps.**


Excellente question ! Le **Nav2 Smoother** s'insère précisément entre le **path planning** (global) et le **motion planning** (local/contrôle). C'est l'étape intermédiaire qui manquait dans notre discussion précédente.

Voici son rôle exact et pourquoi il est indispensable.

### 1. Où se situe le Smoother dans la pipeline ?

La chaîne de navigation dans Nav2 ressemble à ceci :

**Planificateur Global (Path Planning)** ➡️ **Smoother** ➡️ **Contrôleur (Motion Planning)** ➡️ **Robot**

1.  **Path Planning (A\*, Hybrid-A\*, etc.)** : Trouve un chemin topologique. Il vous dit *par où passer* (ex: "prends le couloir de gauche").
2.  **Smoother** : Prend ce chemin brut et le **lisse géométriquement**. Il vous dit *comment tourner* pour que ce soit fluide.
3.  **Motion Planning (RPP, MPPI, DWA)** : Prend le chemin lissé et génère les commandes de vitesse réelles en gérant les obstacles dynamiques et la cinématique.

### 2. Le problème que le Smoother résout

Les planificateurs globaux comme A\* travaillent sur une **grille discrète** (costmap). Le chemin qu'ils produisent est donc une suite de segments droits avec des **angles très marqués** (souvent à 90°).

Pour un robot, ce chemin brut pose deux problèmes :
- **Cinématique** : Un robot à roues (ou à direction Ackermann) ne peut pas tourner instantanément à 90°. Il a un rayon de braquage.
- **Confort et usure** : Suivre une ligne brisée fait saccader le robot, use les moteurs et consomme plus d'énergie.

Le Smoother va donc **arrondir les angles**, réduire la courbure et créer une trajectoire continue et dérivable.

### 3. Les Smoothers standards dans Nav2

Tout comme pour les planificateurs et les contrôleurs, Nav2 fournit des plugins de lissage prêts à l'emploi. Vous les activez dans un fichier YAML via le `smoother_server`.

Voici les principaux :

- **`nav2_smoother::SimpleSmoother`** : Un lissage basique par moyenne mobile. Rapide, mais ne garantit pas l'évitement d'obstacles.
- **`nav2_smoother::ConstrainedSmoother`** : Le plus utilisé. Il utilise un optimiseur (Ceres Solver) pour minimiser la courbure tout en gardant le chemin à distance des obstacles (via la costmap). C'est le standard pour les robots non-holonomes.
- **`nav2_smoother::SavitzkyGolaySmoother`** : Utilise un filtre polynomial pour lisser le chemin.

### 4. Exemple de configuration YAML

Comme pour le reste de Nav2, vous n'avez pas à coder l'algorithme de lissage. Vous le configurez :

```yaml
smoother_server:
  ros__parameters:
    smoother_plugins: ["SmoothPath"]

    SmoothPath:
      plugin: "nav2_smoother::ConstrainedSmoother"
      max_iterations: 1000
      w_smooth: 0.3
      w_data: 0.2
      tolerance: 1.0e-10
      do_refinement: true
```

### 5. Résumé : Path vs Smoother vs Motion

Pour bien fixer les idées, voici comment les trois s'articulent :

| Étape | Rôle | Sortie | Contraintes principales |
| :--- | :--- | :--- | :--- |
| **Path Planning** | Trouver *où* passer | Chemin brut (waypoints) | Obstacles statiques, topologie |
| **Smoother** | Rendre le chemin *dérivable* | Chemin lissé (courbes) | Courbure, distance aux obstacles |
| **Motion Planning** | Suivre le chemin *en temps réel* | Commandes `cmd_vel` | Dynamique, obstacles dynamiques |

### En résumé

Le **Nav2 Smoother** est le pont entre la géométrie brute du path planning et la dynamique du motion planning. Il ne change pas *où* vous allez (le chemin reste globalement le même), mais il change *comment* vous y allez pour que ce soit physiquement possible et confortable pour le robot.

Si vous utilisez un planificateur global comme `SmacPlannerHybrid` (Hybrid-A\*), sachez qu'il génère déjà des chemins relativement lisses. Le Smoother est surtout critique si vous utilisez un planificateur sur grille simple comme `NavFn` ou `SmacPlanner2D`.


# 🧠 Behavior Tree (BT) dans Nav2 — Synthèse

## 1. Rôle du BT : le chef d'orchestre

Le **Behavior Tree** est le **cerveau décisionnel** de Nav2. Il ne calcule rien lui-même (ni chemin, ni vitesse), mais il **coordonne** tous les serveurs :

- `planner_server` → Path Planning (A\*, Hybrid-A\*)
- `smoother_server` → Lissage du chemin
- `controller_server` → Motion Planning (RPP, MPPI, DWA)
- `behavior_server` → Récupérations (Spin, BackUp, Wait…)

**Flux global :**
```
Goal NavigateToPose
   ⬇
bt_navigator  (exécute le BT)
   ⬇
planner ➡️ smoother ➡️ controller ➡️ recoveries
```

Sans lui, tous ces serveurs seraient isolés et ne sauraient ni **quand** ni **comment** s'appeler.

---

## 2. YAML + XML : complémentaires, pas alternatifs

⚠️ **Les deux sont utilisés en même temps** par le même nœud `bt_navigator`.

| Élément | Fichier | Rôle |
|---|---|---|
| Paramètres `bt_navigator` | **YAML** | *Comment* le nœud fonctionne |
| `default_bt_xml_filename` | **YAML** | Pointeur vers le XML à charger |
| `plugin_lib_names` | **YAML** | Liste des nœuds BT disponibles |
| `<BehaviorTree>` | **XML** | *Quoi* le nœud fait (politique) |

**En une phrase :**
- **YAML** = configuration du nœud (frames, timeouts, fréquence, chemin du XML)
- **XML** = logique de navigation (ordre des actions, récupérations)

Le XML **n'est jamais écrit dans le YAML** : le YAML contient juste un **chemin** vers le fichier XML.

---

## 3. Le YAML typique

```yaml
bt_navigator:
  ros__parameters:
    use_sim_time: true
    global_frame: map
    robot_base_frame: base_link
    odom_topic: /bumperbot_controller/odom
    transform_tolerance: 0.3
    default_server_timeout: 1000
    bt_loop_duration: 10
    wait_for_service_timeout: 1000
    default_bt_xml_filename: "navigate_to_pose_w_replanning_and_recovery.xml"
    plugin_lib_names:
      - nav2_compute_path_to_pose_action_bt_node
      - nav2_follow_path_action_bt_node
      - nav2_spin_action_bt_node
      - nav2_wait_action_bt_node
      - nav2_back_up_action_bt_node
      - nav2_clear_costmap_service_bt_node
```

⚠️ **Sans `default_bt_xml_filename`, `bt_navigator` ne sait pas quel arbre charger.** C'est ce paramètre qui fait le pont YAML ↔ XML.

---

## 4. Le XML typique (simplifié)

```xml
<root>
  <BehaviorTree ID="MainTree">
    <RecoveryNode number_of_retries="6" name="NavigateRecovery">
      <PipelineSequence name="NavigateWithReplanning">
        <RateController hz="1.0">
          <ComputePathToPose goal="{goal}" path="{path}"/>
        </RateController>
        <FollowPath path="{path}"/>
      </PipelineSequence>
      <ReactiveFallback name="RecoveryFallback">
        <GoalUpdated/>
        <Sequence name="RecoveryActions">
          <ClearEntireCostmap name="ClearLocalCostmap"/>
          <Spin spin_dist="1.57"/>
          <Wait wait_duration="5.0"/>
          <BackUp backup_dist="0.3"/>
        </Sequence>
      </ReactiveFallback>
    </RecoveryNode>
  </BehaviorTree>
</root>
```

**Lecture :**
- **`RecoveryNode`** : tente la navigation, puis les récupérations (6 essais max).
- **`PipelineSequence`** : planifie (1 Hz) + suit le chemin en parallèle.
- **`ComputePathToPose`** → appelle `planner_server`.
- **`FollowPath`** → appelle `controller_server`.
- **`ReactiveFallback`** : si échec → GoalUpdated, ClearCostmap, Spin, Wait, BackUp.

---

## 5. Les 3 types de nœuds BT

- **Contrôle** : `Sequence` (ordre strict), `Fallback` (essaie dans l'ordre), `PipelineSequence`, `RateController`.
- **Action** : appellent un serveur Nav2 (`ComputePathToPose`, `FollowPath`, `Spin`…).
- **Condition** : vérifient un état (`GoalUpdated`, `IsPathValid`…).

---

## 6. Quand est-ce utilisé ?

À **chaque goal de navigation** :

1. Goal publié sur `/navigate_to_pose`.
2. `bt_navigator` **instancie le BT** décrit dans le XML.
3. Il "tick" le BT toutes les `bt_loop_duration` ms.
4. À chaque tick : évalue les nœuds, appelle les serveurs, gère les échecs.
5. Le goal se termine en **SUCCESS** ou **FAILURE**.

---

## 7. Launch file

```python
bt_navigator = Node(
    package='nav2_bt_navigator',
    executable='bt_navigator',
    name='bt_navigator',
    output='screen',
    parameters=[bt_navigator_params]  # YAML avec default_bt_xml_filename
)
```

---

## 8. Pourquoi c'est puissant

- **Modulaire** : changer la logique sans recompiler.
- **Lisible** : un XML décrit la politique clairement.
- **Réactif** : gère événements et échecs en temps réel.
- **Extensible** : on peut créer ses propres nœuds BT custom.

---

## 9. Où modifier quoi ?

| Objectif | Fichier à éditer |
|---|---|
| Changer la fréquence / les frames | **YAML** |
| Changer l'ordre des actions | **XML** |
| Ajouter une récupération custom | **XML** (+ plugin custom) |
| Pointer vers un autre BT | **YAML** (`default_bt_xml_filename`) |

---

## 10. Récap architecture Nav2

| Composant | Rôle |
|---|---|
| **`bt_navigator`** | Orchestre la navigation via le BT |
| **`planner_server`** | Path Planning |
| **`smoother_server`** | Lissage |
| **`controller_server`** | Motion Planning |
| **`behavior_server`** | Récupérations |
| **`costmap_2d`** | Représentation de l'environnement |

---

**À retenir :**
> Le **YAML** dit *comment* `bt_navigator` fonctionne.
> Le **XML** dit *quoi* il fait.
> Les deux sont chargés **au lancement** et utilisés **à chaque goal**.
> On ne choisit pas l'un ou l'autre : **on a besoin des deux**.


Le **`behavior_server`** est le **bras armé** de la navigation dans Nav2. Si le `bt_navigator` est le chef d'orchestre (le cerveau qui décide), le `behavior_server` est l'**ouvrier spécialisé** qui exécute les manœuvres de secours et les comportements simples lorsque la navigation normale échoue.

Voici son rôle exact et comment il s'intègre dans l'architecture.

### 1. Rôle principal : Gérer les récupérations (Recoveries)

Le `behavior_server` n'est **pas** utilisé pour se déplacer d'un point A à un point B. Son rôle est de gérer les **comportements d'urgence** ou **de dégagement** quand le robot est bloqué, perdu, ou que le contrôleur échoue.

Il fournit des **serveurs d'action** (Action Servers) que le Behavior Tree (BT) peut appeler à tout moment. Par exemple, si le robot ne peut pas avancer, le BT va appeler le `behavior_server` pour :
- **Tourner sur place** (`Spin`) pour dégager le lidar ou se relocaliser.
- **Reculer** (`BackUp`) pour sortir d'un cul-de-sac.
- **Attendre** (`Wait`) quelques secondes pour laisser passer un obstacle dynamique.
- **Avancer en ligne droite** (`DriveOnHeading`) pour un petit ajustement.

### 2. Les comportements standards (Plugins)

Comme pour le reste de Nav2, le `behavior_server` charge des **plugins**. Voici les plus courants :

- **`nav2_behaviors::Spin`** : Fait tourner le robot sur lui-même d'un angle donné.
- **`nav2_behaviors::BackUp`** : Fait reculer le robot sur une distance donnée.
- **`nav2_behaviors::DriveOnHeading`** : Fait avancer le robot en ligne droite sur une distance donnée.
- **`nav2_behaviors::Wait`** : Met le robot en pause pendant une durée définie.
- **`nav2_behaviors::AssistedTeleop`** : Permet à un opérateur de reprendre la main manuellement (via téléopération) tout en gardant les sécurités actives.

### 3. Comment il s'articule avec le Behavior Tree

C'est ici que le lien avec votre question précédente est crucial. Le `behavior_server` **ne décide pas** quand agir. C'est le **BT** qui décide.

Dans le fichier XML du BT, vous avez des nœuds d'action comme :
```xml
<Spin spin_dist="1.57"/>
<Wait wait_duration="5.0"/>
<BackUp backup_dist="0.3"/>
```

Ces nœuds XML ne contiennent pas la logique de rotation ou de recul. Ils envoient simplement une **requête d'action** au `behavior_server`. Ce dernier exécute le mouvement réel en publiant des commandes de vitesse (`cmd_vel`) et en vérifiant que le robot ne collisionne pas.

### 4. Différence avec le `controller_server`

Il est important de ne pas les confondre :

| Composant | Rôle | Exemple |
| :--- | :--- | :--- |
| **`controller_server`** | Suit un chemin planifié (Motion Planning) | "Suis cette trajectoire lissée pour aller au goal" |
| **`behavior_server`** | Exécute des manœuvres prédéfinies (Récupération) | "Tourne sur toi-même de 90° car tu es bloqué" |

Le `controller_server` est **continu** (il tourne à 20 Hz pour suivre le chemin). Le `behavior_server` est **ponctuel** (il exécute une action, puis s'arrête).

### 5. Configuration YAML typique

Dans votre fichier de paramètres Nav2, vous trouverez un bloc comme celui-ci :

```yaml
behavior_server:
  ros__parameters:
    costmap_topic: local_costmap/costmap_raw
    footprint_topic: local_costmap/published_footprint
    cycle_frequency: 10.0
    behavior_plugins: ["spin", "backup", "drive_on_heading", "wait"]
    spin:
      plugin: "nav2_behaviors/Spin"
    backup:
      plugin: "nav2_behaviors/BackUp"
    drive_on_heading:
      plugin: "nav2_behaviors/DriveOnHeading"
    wait:
      plugin: "nav2_behaviors/Wait"
    global_frame: odom
    robot_base_frame: base_link
    transform_tolerance: 0.1
    use_sim_time: true
    simulate_ahead_time: 2.0
    max_rotational_vel: 1.0
    min_rotational_vel: 0.4
    rotational_acc_lim: 3.2
```

### 6. Résumé

Le **`behavior_server`** est la **boîte à outils de secours** de Nav2. Il fournit des actions simples et robustes (tourner, reculer, attendre) que le **Behavior Tree** peut déclencher quand la navigation normale échoue.

- **Il ne planifie pas** (ce n'est pas le `planner_server`).
- **Il ne suit pas de chemin** (ce n'est pas le `controller_server`).
- **Il exécute des comportements prédéfinis** sur ordre du BT.

En clair : le `bt_navigator` dit *"on est bloqué, il faut reculer"*, et le `behavior_server` est celui qui **fait réellement reculer le robot**.