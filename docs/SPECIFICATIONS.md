# 📘 Specification: Document Tagging & Access System for Agentic Interactions

## ✅ Purpose

Enable users and admins to **organize, share, and scope documents** for agent usage through a **general-purpose tag system** with access control.

---

## 🧱 Core Concepts

### 1. Tag

- A reusable semantic label (e.g. `project-mars`, `client-thales`, `private-session-abc`).
- Tags group documents into shared or private contexts.
- Tags are permissioned — users can only see/use tags they have access to.

### 2. Document

- Uploaded by a user (stored in MinIO or similar).
- Metadata includes filename, size, owner, and associated tags.
- Can belong to multiple tags.
- May have derived artifacts: markdown, vector index, previews.

### 3. Artifact

- A derived output from the raw document.
- Types: `markdown`, `vector`, `preview`, etc.
- Linked to the source document.

### 4. User-Tag Permission

- Defines which users can access which tags.
- Permissions: `read`, `write`, `admin`.
- Used to control both document visibility and tagging rights.

---

## 🔄 Document Contexts

| Context Type              | Description                                                                 |
|---------------------------|-----------------------------------------------------------------------------|
| Shared (project/workspace)| A document tagged with one or more **shared tags**, available to others     |
| Private (conversation)    | A document uploaded during a session, tagged with a **private session tag** |

---

## 🧑‍💻 Role-Based UI Capabilities

| Action                                                       | Admin                 | Regular User           |
|--------------------------------------------------------------|------------------------|-------------------------|
| Create / Delete Tags                                         | ✅                     | ❌                      |
| Assign Tags to Documents                                     | ✅ (any tag)           | ✅ (only permitted tags)|
| Grant/Revoke Tag Permissions to Users                        | ✅                     | ❌                      |
| Upload Document (Shared Context)                             | ✅                     | ✅                      |
| Upload Document (Private Session)                            | ✅                     | ✅                      |
| Tag Document During Upload                                   | ✅                     | ✅ (within scope)       |
| View and Filter Documents by Tags                            | ✅                     | ✅ (with read access)   |
| Select/Unselect Tagged Documents for Agent Interaction       | ✅                     | ✅                      |
| Delete Document (Owned or Admin)                             | ✅                     | ✅ (if owner)           |
| Manage Derived Artifacts (trigger reprocessing, view logs)   | ✅                     | ❌ (view-only)          |

---

## 🎯 Key UX Use Cases

- **Upload for collaboration**: A user uploads a document and assigns it to `project-mars`. Others with access to that tag can now reference it in agent interactions.
- **Upload for a session**: A user drops a file during a private agent chat. It gets tagged under a private session tag (`private-user123-session456`) and used transiently.
- **Restrict scope**: In the agent UI, a user selects only documents tagged with `project-mars` and `client-briefing` to get precise answers.
- **Broaden scope**: The same user later includes `tech-specs` and `previous-contracts` tags to include a wider document base.

---
