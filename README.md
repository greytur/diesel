# DIESEL PROJECT
**Diesel** is an easy-to-use wrapper and extension for DearPyGUI that streamlines the frustrating parts of the framework for developers.

### What makes Diesel so easy to use?
Diesel aims to be as minimally intrusive towards ALL existing DearPyGUI projects, thus it replaces the standard `dpg` with `dsl` whilst retaining ALL standard framework functionality!

- `import dearpygui.dearpygui as dpg` becomes `import diesel as dsl`
- `dpg.(Anything)` works with `dsl.(Anything)` with no development headaches!
- Diesel Features are OPT-IN, meaning that anything added will not affect your current project! 
    - You can even use `import diesel as dpg` instead!

### What aspects does Diesel aim to embody?
Diesel aims to be easy to use, dynamic under the hood, and streamlined for the GUI developer experience.

## What features does Diesel offer or plan to?
Diesel's primary purpose is to streamline the interface customization experience, commonly called "theming" or "themes" by DearPyGUI.

It does this through YAML files that are written in a particular format understood by Diesel's internals. This Psuedo-DSL (Domain Specific Language) was chosen due to it's superior readability to JSON or TOML for the intended purpose.

Diesel aims to offer developers the ability to fine-tune the syntax and inner workings of the "engine" if they so desire (names, shortcuts, etc)!

VS Code supports custom format YAML autocomplete via the RedHat extension, and Diesel aims to easily hook into this ability and provide syntax & docstring hints & more!

Much more is in the works beyond customization and theming, I hope to be able to offer a form of UI-layout syntax in the future, add additional python functionality & QOL, supplementary DPG Documentation and much more! 
## About the Project
This project is a revival of a former personal project that I left far from fully implemented.

Given DIESEL's active state of heavy modification and development, do not expect most features to be reliable or consistent.

- The target Internal Version for semi-stable public use is expected to be when Internal Version 4 is RELEASED.
- The current Internal Version by RELEASE is Internal Version 2
- Internal Version 3 is close to being ready for release.
- Expect Internal Version 4 to be functional by the end of June 2026.
- The timeline for Internal Version 5 is TBD.

## Current Version Note
This version does not contain the `/docs` folder that actually contains documentation.

The current documentation is not in a stable state given the frequent modifications made to the actual codebase, keeping up with (for other's viewing needs) burdens my development times at this stage in the project.

Furthermore, though there is a significant amount of documentation I have made for MY needs, it would be unwise to release it at this time.

Documentation will be published within the set development milestone (Internal Version 4) 

## Project Goal
For all intents & purposes, `diesel` has been through enough brainstorming to 
power a small city, and has faced enough redesigns that the "main" concept has
effectively been forgotten. 

As a result of this, the first "goal" that the revamp(s) will attempt to tackle is
the completion of the "aggregator" portion of the code. This code has seen the 
most redesign, and formerly went under the names "autobuilder" or "builder".

### Aggregator
- [x] Aggregator Redesign v1 (Internal Version 2)
- [x] Aggregator Working MVP (Internal Version 3)
- [ ] Aggregator Redesign v2 (Internal Version 4)

### Engine
- [x] Engine Initial Design & Rewrite (Internal Version 2)
- [x] Engine Integrated & Working MVP (Internal Version 3)
- [ ] Engine Rework & Link Aggregator (Internal Version 4)
- [ ] Engine Capabilities +Refinement (Internal Version 5)

### Documentation
- [x] Docs on direct usage of `__main__.py`
- [x] Docs on logic and design of `dpg_item_classifier.py`
- [x] Docs on legacy porting of the formerly used code (Internal Version 1)
- [x] Docs on long-term planning of the project
- [x] Docs on naming logic
- [x] Docs as comments in python files for simple understanding and recall
- [ ] Docs on full DIESEL usage (Internal Version 4)
- [ ] Public usage documentation release (Internal Version 4)