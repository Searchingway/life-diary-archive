cmake_minimum_required(VERSION 3.22)

project(LifeDiaryMobile VERSION 1.5.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Qt6 6.5 REQUIRED COMPONENTS Core Quick QuickControls2 QuickDialogs2 Qml)

qt_standard_project_setup(REQUIRES 6.5)
qt_policy(SET QTP0004 NEW)

qt_add_executable(LifeDiaryMobile
    MANUAL_FINALIZATION
    src/ArchiveStore.cpp
    src/ArchiveStore.h
    src/main.cpp
)

qt_add_qml_module(LifeDiaryMobile
    URI LifeDiaryMobile
    VERSION 1.0
    QML_FILES
        qml/Main.qml
        qml/HomePage.qml
        qml/DiaryPage.qml
        qml/FootprintPage.qml
        qml/BookPage.qml
        qml/PlanPage.qml
        qml/LightThoughtPage.qml
        qml/LightResourcePage.qml
        qml/SelfObservationPage.qml
        qml/DataManagerPage.qml
        qml/components/FieldLabel.qml
        qml/components/ImageListEditor.qml
        qml/components/RecordCard.qml
        qml/components/SectionTitle.qml
)

target_link_libraries(LifeDiaryMobile
    PRIVATE
        Qt6::Core
        Qt6::Quick
        Qt6::QuickControls2
        Qt6::QuickDialogs2
        Qt6::Qml
)

if(ANDROID)
    set_target_properties(LifeDiaryMobile PROPERTIES
        QT_ANDROID_PACKAGE_NAME "com.localfirst.lifediary"
        QT_ANDROID_APP_NAME "人生档案"
        QT_ANDROID_APP_ICON "@mipmap/ic_launcher"
        QT_ANDROID_PACKAGE_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/android"
        QT_ANDROID_MIN_SDK_VERSION 27
        QT_ANDROID_VERSION_CODE 1
        QT_ANDROID_VERSION_NAME "${PROJECT_VERSION}"
    )
endif()

qt_finalize_executable(LifeDiaryMobile)
