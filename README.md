# Flask & Kubernetes Progressive Delivery Demo 🚀

This project is a comprehensive demo illustrating how to use **Kubernetes**, **Argo Rollouts**, and **Flask** together to provide a **Progressive Delivery** experience based on RBAC and Cookies to route traffic between application versions.

## 🎯 Project Concept
Instead of releasing updates to all users at once, this system allows you to:
1. Keep regular users on the **Stable Release (V1)**.
2. Allow Developers to test the **New Release (V2 Canary)** on the exact same production URL via a login system that plants a specific `Cookie` in their browser.
3. Automatically send Kubernetes Events (who visited the page, etc.) directly from within the Pod itself!

---

## 🔐 What are the "Accounts" & RBAC used in this system?
In Kubernetes, Pods do not have default permissions to talk to the API Server and make changes. Since our Flask app needs to send `Events` to K8s to say "a visitor just accessed my page", we needed to create **custom accounts and permissions (RBAC)**. These are divided into three parts (found in `rbac.yaml`):

1. **ServiceAccount (`flask-demo-sa`)**:
   This acts as the "Identity" or ID card we give to the Flask application. When Flask talks to Kubernetes, K8s will recognize it through this account.
2. **Role (`flask-demo-event-creator`)**:
   Here we define "What can this identity do?". We created a role that only allows (`create`, `patch`, `update`) for resources of type `events` within the Namespace. We did not grant permissions to delete or modify anything else to ensure strict security.
3. **RoleBinding (`flask-demo-event-creator-binding`)**:
   This is the contract that binds the Identity (ServiceAccount) to the Permissions (Role). It tells K8s that the application holding the `flask-demo-sa` identity is authorized to exercise the `flask-demo-event-creator` role.

Through these "Accounts", the Python code inside Flask can use `config.load_incluster_config()` to automatically inherit these permissions and send Events securely!

---

## 🛠️ How to Run the Demo (Step-by-Step)

### 1. Build the Docker Images
Open your terminal and run the CI simulation script we created to build both versions:
```bash
./build_ci.sh
```
*(Note: If you are using `minikube` or `kind`, remember to load the images into your cluster, e.g.: `minikube image load taha/flask-demo:v1 taha/flask-demo:v2`)*

### 2. Install the Project using Helm
Ensure that **Argo Rollouts** and **NGINX Ingress Controller** are installed in your Cluster.
Then, install the application (it will start as V1):
```bash
helm upgrade --install my-flask-demo ./chart/flask-demo
```

### 3. Setup your Host (Local Access)
Open the `/etc/hosts` file on your system, and add the following line (change `127.0.0.1` to your Ingress IP if necessary):
```text
127.0.0.1 demo.local
```

### 4. Test Progressive Delivery (User vs Developer)
1. Open your browser and go to: `http://demo.local`
2. The login page (Role Selection) will appear.
3. Click on **"Enter as Normal User"**. The system will give you a regular user `Cookie`, and you will see the stable blue **V1** dashboard.
4. **How to release V2?** Open `chart/flask-demo/values.yaml` and change `tag: "v1"` to `tag: "v2"`.
5. Run the upgrade:
   ```bash
   helm upgrade my-flask-demo ./chart/flask-demo
   ```
6. **Argo Rollouts** will start preparing the Canary but will `pause`. Normal users will not be affected.
7. Now open your browser again at `http://demo.local` and click **"Enter as Developer"**. The browser will save the developer `Cookie`... Wow! You are instantly routed to the purple **V2** developer dashboard!

### 5. Monitor the Events
To see the Events sent by the Pod thanks to the "Accounts" we created, run:
```bash
kubectl get events --sort-by='.metadata.creationTimestamp'
```
You will see events named `flask-app-event-...` notifying you about every visitor!
