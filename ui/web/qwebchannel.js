// qwebchannel.js — Qt 6 WebChannel client (official, minified-compatible)
"use strict";
var QWebChannelMessageTypes = {
    signal: 1, propertyUpdate: 2, init: 3, idle: 4,
    debug: 5, invokeMethod: 6, connectToSignal: 7,
    disconnectFromSignal: 8, setProperty: 9, response: 10,
};
var QWebChannel = function(transport, initCallback) {
    if (typeof transport !== "object" || typeof transport.send !== "function") {
        console.error("QWebChannel: invalid transport"); return;
    }
    var channel = this;
    this.transport = transport;
    this.send = function(data) {
        if (typeof data !== "string") data = JSON.stringify(data);
        channel.transport.send(data);
    };
    this.onmessage = function(message) {
        var data = message.data;
        if (typeof data === "string") data = JSON.parse(data);
        switch (data.type) {
            case QWebChannelMessageTypes.signal:       channel.handleSignal(data); break;
            case QWebChannelMessageTypes.response:     channel.handleResponse(data); break;
            case QWebChannelMessageTypes.propertyUpdate: channel.handlePropertyUpdate(data); break;
            default: console.error("QWebChannel: unhandled message", data);
        }
    };
    this.execCallbacks = {};
    this.execId = 0;
    this.exec = function(data, callback) {
        if (!callback) { channel.send(data); return; }
        if (channel.execId === Number.MAX_VALUE) channel.execId = 0;
        data.id = channel.execId++;
        channel.execCallbacks[data.id] = callback;
        channel.send(data);
    };
    this.objects = {};
    this.handleSignal = function(message) {
        var object = channel.objects[message.object];
        if (object) object.signalEmitted(message.signal, message.args);
    };
    this.handleResponse = function(message) {
        if (message.id === undefined) { console.error("QWebChannel: response missing id"); return; }
        var callback = channel.execCallbacks[message.id];
        if (callback) { delete channel.execCallbacks[message.id]; callback(message.data); }
    };
    this.handlePropertyUpdate = function(message) {
        message.data.forEach(function(data) {
            var object = channel.objects[data.object];
            if (object) object.propertyUpdate(data.signals, data.properties);
        });
    };
    this.debug = function(message) { channel.send({ type: QWebChannelMessageTypes.debug, data: message }); };
    transport.onmessage = this.onmessage;
    this.exec({ type: QWebChannelMessageTypes.init }, function(data) {
        data.forEach(function(classInfo) {
            new QObject(classInfo.name, classInfo, channel);
        });
        Object.freeze(channel.objects);
        if (initCallback) initCallback(channel);
        channel.exec({ type: QWebChannelMessageTypes.idle });
    });
};
function QObject(name, data, webChannel) {
    this.__id__ = name;
    webChannel.objects[name] = this;
    var object = this;
    this.unwrapQObject = function(response) {
        if (response instanceof Array) return response.map(function(qobj){ return object.unwrapQObject(qobj); });
        if (!response || !response["__QObject*__"] || response.id === undefined) return response;
        var objectId = response.id;
        if (webChannel.objects[objectId]) return webChannel.objects[objectId];
        var qObject = new QObject(objectId, response.data, webChannel);
        qObject.destroyed.connect(function() { if (webChannel.objects[objectId] === qObject) delete webChannel.objects[objectId]; });
        return qObject;
    };
    this.propertyUpdate = function(signals, propertyMap) {
        for (var propertyName in propertyMap) {
            if (!propertyMap.hasOwnProperty(propertyName)) continue;
            object[propertyName] = object.unwrapQObject(propertyMap[propertyName]);
        }
        for (var signalName in signals) {
            if (!signals.hasOwnProperty(signalName)) continue;
            object[signalName].emit(signals[signalName]);
        }
    };
    this.signalEmitted = function(signalName, signalArgs) {
        var signal = object[signalName];
        if (signal) signal.emit(object.unwrapQObject(signalArgs));
    };
    function addSignal(signalData, isPropertyNotifySignal) {
        var signalName = signalData[0], signalIndex = signalData[1];
        object[signalName] = {
            connect: function(callback) {
                if (typeof callback !== "function") { console.error("connect: callback must be a function"); return; }
                if (!object.__objectSignals__) object.__objectSignals__ = {};
                if (!object.__objectSignals__[signalIndex]) object.__objectSignals__[signalIndex] = [];
                object.__objectSignals__[signalIndex].push(callback);
                if (!isPropertyNotifySignal && signalName !== "destroyed") {
                    webChannel.exec({ type: QWebChannelMessageTypes.connectToSignal, object: object.__id__, signal: signalIndex });
                }
            },
            disconnect: function(callback) {
                if (!object.__objectSignals__ || !object.__objectSignals__[signalIndex]) return;
                var idx = object.__objectSignals__[signalIndex].indexOf(callback);
                if (idx >= 0) object.__objectSignals__[signalIndex].splice(idx, 1);
                if (object.__objectSignals__[signalIndex].length === 0) {
                    webChannel.exec({ type: QWebChannelMessageTypes.disconnectFromSignal, object: object.__id__, signal: signalIndex });
                }
            },
            emit: function(args) {
                if (!object.__objectSignals__ || !object.__objectSignals__[signalIndex]) return;
                object.__objectSignals__[signalIndex].forEach(function(cb) { cb.apply(object, args); });
            }
        };
    }
    function addMethod(methodData) {
        var methodName = methodData[0], methodIndex = methodData[1];
        object[methodName] = function() {
            var args = [], callback, errCb;
            Array.prototype.forEach.call(arguments, function(arg) {
                if (typeof arg === "function") { if (!callback) callback = arg; else errCb = arg; }
                else args.push(arg);
            });
            webChannel.exec({ type: QWebChannelMessageTypes.invokeMethod, object: object.__id__, method: methodIndex, args: args },
                function(response) {
                    if (response !== undefined) {
                        var result = object.unwrapQObject(response);
                        if (callback) callback(result);
                    } else if (errCb) { errCb(); }
                });
        };
    }
    data.methods.forEach(addMethod);
    data.signals.forEach(function(s) { addSignal(s, false); });
    data.properties.forEach(function(propertyInfo) {
        var propertyName = propertyInfo[0], notifySignalData = propertyInfo[2];
        if (notifySignalData) addSignal(notifySignalData, true);
        object[propertyName] = propertyInfo[3];
    });
}
