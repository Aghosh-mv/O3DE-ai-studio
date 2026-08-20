"""
Copyright (c) Contributors to the Open 3D Engine Project.
For complete copyright and license terms please see the LICENSE at the root of this distribution.

SPDX-License-Identifier: Apache-2.0 OR MIT
"""

import sys
import os
import azlmbr
import azlmbr.bus


params = azlmbr.qt.QtForPythonRequestBus(azlmbr.bus.Broadcast, 'GetQtBootstrapParameters')

if len(params.qtPluginsFolder):
    # add the Qt plugins to the environment
    os.environ['QT_PLUGIN_PATH'] = params.qtPluginsFolder

# add Qt binaries to the Windows path to handle findings DLL file dependencies
if len(params.qtBinaryFolder) and sys.platform.startswith('win'):
    path = os.environ['PATH']
    newPath = ''
    newPath += params.qtBinaryFolder + os.pathsep
    newPath += path
    os.environ['PATH'] = newPath
    print('PySide bootstrapped PATH for Windows.')

    # Once PySide has been bootstrapped, register our Object Tree visualizer with the Editor
    try:
        import az_qt_helpers
        from show_object_tree import ObjectTreeDialog
        az_qt_helpers.register_view_pane('Object Tree', ObjectTreeDialog)
    except:
        print('Skipping register our Object Tree visualizer with the Editor.')

    # Register AI Design Studio sidebar
    try:
        import sys
        # Find AI Design Studio scripts - check multiple locations
        script_dir = os.path.dirname(os.path.abspath(__file__))
        possible_paths = [
            os.path.join(script_dir, '..', '..', '..', 'AIDesignStudio', 'Editor', 'Scripts'),
            os.path.join(script_dir, '..', '..', '..', '..', 'Gems', 'AIDesignStudio', 'Editor', 'Scripts'),
            os.path.join(script_dir, '..', '..', '..', '..', 'AISidebar'),
        ]
        for ai_path in possible_paths:
            ai_path = os.path.normpath(ai_path)
            if os.path.isdir(ai_path) and ai_path not in sys.path:
                sys.path.insert(0, ai_path)
                break
        import az_qt_helpers
        from ai_sidebar import AISidebarPanel
        az_qt_helpers.register_view_pane('AI Design Studio', AISidebarPanel, category='AI Tools')
        print('AI Design Studio registered successfully!')
    except Exception as e:
        print(f'Skipping AI Design Studio registration: {e}')

