# 🎯 Guide QoS ROS 2 — Robot Autonome
### Référence quotidienne pour choisir la bonne QoS selon le capteur

---

## 1. Les 4 piliers de la QoS (à connaître par cœur)

| Pilier | Question à laquelle il répond | Valeurs possibles |
|---|---|---|
| **Reliability** | Un message peut-il être perdu ? | `RELIABLE` / `BEST_EFFORT` |
| **Durability** | Un nouveau subscriber reçoit-il le passé ? | `VOLATILE` / `TRANSIENT_LOCAL` |
| **History** | Combien de messages garder en mémoire ? | `KEEP_LAST(n)` / `KEEP_ALL` |
| **Depth** | Taille de la file si `KEEP_LAST` | entier (souvent 1, 5, 10) |

> **Règle d'or de compatibilité** : le **subscriber** doit être **au moins aussi permissif** que le **publisher**. Sinon → 0 message reçu, sans erreur bruyante (juste un warning "incompatible QoS").

### Tableau de compatibilité Reliability

| Publisher \ Subscriber | RELIABLE | BEST_EFFORT |
|---|---|---|
| **RELIABLE** | ✅ | ✅ |
| **BEST_EFFORT** | ❌ | ✅ |

### Tableau de compatibilité Durability

| Publisher \ Subscriber | TRANSIENT_LOCAL | VOLATILE |
|---|---|---|
| **TRANSIENT_LOCAL** | ✅ | ✅ |
| **VOLATILE** | ❌ | ✅ |

---

## 2. 🧭 Arbre de décision rapide

```
Le message peut-il être perdu sans conséquence grave ?
│
├─ OUI → BEST_EFFORT
│         (capteur haute fréquence, flux continu : scan, image, IMU brute)
│
└─ NON → RELIABLE
          │
          Le topic est-il publié une seule fois / rarement (donnée statique) ?
          │
          ├─ OUI → + TRANSIENT_LOCAL  (map, tf_static, robot_description)
          │
          └─ NON → + VOLATILE  (cmd_vel, odom, amcl_pose fiable, diagnostics)
```

---

## 3. 📋 Tableau maître par capteur / topic

| Capteur / Topic | Fréquence typique | Reliability | Durability | Depth | Pourquoi |
|---|---|---|---|---|---|
| **LiDAR** `/scan` | 5–40 Hz | `BEST_EFFORT` | `VOLATILE` | 5 | Flux continu, perte tolérable |
| **LiDAR 3D** `/points` (PointCloud2) | 10–20 Hz | `BEST_EFFORT` | `VOLATILE` | 5 | Volumineux, haute fréquence |
| **Caméra** `/image_raw` | 15–60 Hz | `BEST_EFFORT` | `VOLATILE` | 5 | Idem, standard `sensor_data` |
| **Caméra** `/camera_info` | idem image | `BEST_EFFORT` | `VOLATILE` | 5 | Doit matcher l'image associée |
| **IMU** `/imu/data` | 50–200 Hz | `BEST_EFFORT` | `VOLATILE` | 10 | Très haute fréquence, perte OK |
| **GPS** `/fix` (NavSatFix) | 1–10 Hz | `BEST_EFFORT`* | `VOLATILE` | 5 | *Reliable si peu fréquent et critique |
| **Encodeurs / roues** `/wheel_odom` | 20–50 Hz | `RELIABLE` | `VOLATILE` | 10 | Sert à l'odométrie, mieux vaut fiable |
| **Odométrie fusionnée** `/odom` | 20–50 Hz | `RELIABLE` | `VOLATILE` | 10 | Utilisée par la navigation, doit être fiable |
| **Ultrasons / IR** `/range` | 10–20 Hz | `BEST_EFFORT` | `VOLATILE` | 5 | Capteur de proximité, flux continu |
| **Batterie** `/battery_state` | 1 Hz | `RELIABLE` | `VOLATILE` | 1 | Basse fréquence, info importante |
| **AMCL pose** `/amcl_pose` | ~1 Hz | `BEST_EFFORT` (défaut Nav2) | `VOLATILE` | 5 | Remplacée vite si perdue |
| **Particle cloud** `/particle_cloud` | 5–10 Hz | `BEST_EFFORT` | `VOLATILE` | 5 | Visualisation seulement |
| **Carte** `/map` | 1 fois (ou à la demande) | `RELIABLE` | `TRANSIENT_LOCAL` | 1 | Doit atteindre tout nouveau subscriber |
| **Coûts / costmap** `/local_costmap`, `/global_costmap` | continu | `RELIABLE` | `VOLATILE` | 1 | Mise à jour permanente |
| **TF dynamique** `/tf` | 50–100 Hz | `RELIABLE` | `VOLATILE` | 100 | Critique pour les transformations |
| **TF statique** `/tf_static` | 1 fois | `RELIABLE` | `TRANSIENT_LOCAL` | 1 | Doit être vu par tous, même en retard |
| **Description robot** `/robot_description` | 1 fois | `RELIABLE` | `TRANSIENT_LOCAL` | 1 | Chargé une fois, lu par tous les outils |
| **Commande vitesse** `/cmd_vel` | 10–50 Hz | `RELIABLE` | `VOLATILE` | 10 | Une commande perdue = comportement dangereux |
| **Objectifs de nav** `/goal_pose` | rare, événementiel | `RELIABLE` | `VOLATILE` | 1 | Ne doit jamais être perdu |
| **Plan / trajectoire** `/plan` | à chaque replanification | `RELIABLE` | `VOLATILE` | 1 | Doit être livré |
| **Marqueurs RViz** `/markers` | variable | `BEST_EFFORT` | `VOLATILE` | 5 | Purement visuel |
| **Diagnostics** `/diagnostics` | 1 Hz | `RELIABLE` | `VOLATILE` | 10 | Ne doit pas être perdu |
| **Logs / rosout** `/rosout` | événementiel | `RELIABLE` | `VOLATILE` | 100 | Historique de logs |

---

## 4. 🏗️ Les profils QoS prédéfinis (ROS 2 / rclcpp / rclpy)

Plutôt que de tout configurer à la main, utilise ces profils standards :

| Profil | Reliability | Durability | Usage |
|---|---|---|---|
| `rclcpp::SensorDataQoS()` | BEST_EFFORT | VOLATILE | Tous les capteurs haute fréquence |
| `rclcpp::SystemDefaultsQoS()` | RELIABLE | VOLATILE | Topics classiques (cmd_vel, odom) |
| `rclcpp::ServicesQoS()` | RELIABLE | VOLATILE | Services |
| `rclcpp::ParametersQoS()` | RELIABLE | VOLATILE | Paramètres dynamiques |
| Profil "map-like" (custom) | RELIABLE | **TRANSIENT_LOCAL** | map, tf_static, robot_description |

### Exemple C++ (rclcpp)

```cpp
// Capteur (LiDAR, caméra, IMU...)
auto scan_pub = this->create_publisher<sensor_msgs::msg::LaserScan>(
    "/scan", rclcpp::SensorDataQoS());

// Donnée statique (map)
rclcpp::QoS map_qos(1);
map_qos.reliable().transient_local();
auto map_pub = this->create_publisher<nav_msgs::msg::OccupancyGrid>(
    "/map", map_qos);

// Commande critique
auto cmd_vel_pub = this->create_publisher<geometry_msgs::msg::Twist>(
    "/cmd_vel", rclcpp::QoS(10)); // Reliable + Volatile par défaut
```

### Exemple Python (rclpy)

```python
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, qos_profile_sensor_data

# Capteur
self.scan_sub = self.create_subscription(
    LaserScan, '/scan', self.callback, qos_profile_sensor_data)

# Donnée statique (map)
map_qos = QoSProfile(depth=1)
map_qos.reliability = ReliabilityPolicy.RELIABLE
map_qos.durability = DurabilityPolicy.TRANSIENT_LOCAL
self.map_sub = self.create_subscription(
    OccupancyGrid, '/map', self.map_callback, map_qos)
```

---

## 5. 🔍 Commandes de diagnostic (à utiliser dès qu'un topic "ne passe pas")

```bash
# Voir la QoS réelle d'un topic publié
ros2 topic info /scan --verbose

# Lister tous les topics actifs
ros2 topic list

# Voir si un message arrive vraiment
ros2 topic hz /scan
ros2 topic echo /amcl_pose

# Voir les nœuds et leurs QoS depuis rqt
rqt_graph
```

**Symptôme classique d'un mismatch QoS** : aucun message n'arrive, aucune erreur explicite, juste un warning du type :
```
New publisher discovered on topic '/scan', offering incompatible QoS.
```

---

## 6. ⚠️ Pièges classiques à connaître

| Piège | Cause | Solution |
|---|---|---|
| RViz n'affiche pas `/scan`, `/particle_cloud`, `/amcl_pose` | RViz est en `RELIABLE` par défaut, le publisher est en `BEST_EFFORT` | Passer le display RViz en `BEST_EFFORT` |
| RViz n'affiche pas `/map` alors que map_server tourne | `/map` était en `VOLATILE`, RViz s'est abonné trop tard | Vérifier que `/map` est bien en `TRANSIENT_LOCAL` |
| `/cmd_vel` parfois "perdu" | Publisher en `BEST_EFFORT` par erreur | Toujours `RELIABLE` pour les commandes |
| Nœud qui rejoint tardivement ne voit pas `/tf_static` | Publisher pas en `TRANSIENT_LOCAL` | Vérifier la QoS du broadcaster statique |
| Grosse charge réseau avec beaucoup de robots | `KEEP_ALL` ou `depth` trop grand sur un flux haute fréquence | Utiliser `KEEP_LAST` avec un depth raisonnable (5–10) |

---

## 7. 🧠 Mnémotechnique à retenir chaque jour

> **"Capteur qui parle vite → Best Effort. Donnée qui compte → Reliable. Donnée écrite une fois au tableau → Transient Local."**

- 🔊 **Flux continu haute fréquence** (scan, image, IMU, ultrasons) → `BEST_EFFORT` + `VOLATILE`
- 🎯 **Commandes et décisions critiques** (cmd_vel, goal_pose, plan) → `RELIABLE` + `VOLATILE`
- 🗺️ **Données statiques publiées une fois** (map, tf_static, robot_description) → `RELIABLE` + `TRANSIENT_LOCAL`
- 📊 **États importants mais peu fréquents** (battery, diagnostics, odom fiable) → `RELIABLE` + `VOLATILE`

---

## 8. Cheat sheet finale (à imprimer / garder en favori)

```
┌─────────────────────────────────────────────────────────────┐
│  TYPE DE DONNÉE           →  RELIABILITY   +  DURABILITY     │
├─────────────────────────────────────────────────────────────┤
│  Scan LiDAR / Caméra/IMU  →  BEST_EFFORT   +  VOLATILE       │
│  Ultrasons / Range        →  BEST_EFFORT   +  VOLATILE       │
│  Particle cloud / Markers →  BEST_EFFORT   +  VOLATILE       │
│  Odométrie / AMCL pose    →  RELIABLE*     +  VOLATILE       │
│  cmd_vel / goal_pose      →  RELIABLE      +  VOLATILE       │
│  Diagnostics / Battery    →  RELIABLE      +  VOLATILE       │
│  TF dynamique             →  RELIABLE      +  VOLATILE       │
│  Map / TF static / URDF   →  RELIABLE      +  TRANSIENT_LOCAL│
└─────────────────────────────────────────────────────────────┘
  * dépend du package (Nav2 AMCL publie souvent en BEST_EFFORT)
```

---

*Guide basé sur les principes DDS/ROS 2 — à adapter selon la config réelle de tes drivers (vérifie toujours avec `ros2 topic info --verbose`).*