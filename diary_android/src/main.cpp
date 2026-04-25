#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QQmlContext>
#include <QQuickStyle>

#include "ArchiveStore.h"

int main(int argc, char *argv[])
{
    QGuiApplication app(argc, argv);
    QGuiApplication::setApplicationName(QStringLiteral("人生档案"));
    QGuiApplication::setOrganizationName(QStringLiteral("LocalFirst"));
    QQuickStyle::setStyle(QStringLiteral("Material"));

    ArchiveStore store;

    QQmlApplicationEngine engine;
    engine.rootContext()->setContextProperty(QStringLiteral("archiveStore"), &store);

    QObject::connect(
        &engine,
        &QQmlApplicationEngine::objectCreationFailed,
        &app,
        []() { QCoreApplication::exit(-1); },
        Qt::QueuedConnection);

    engine.loadFromModule(QStringLiteral("LifeDiaryMobile"), QStringLiteral("Main"));
    return app.exec();
}
