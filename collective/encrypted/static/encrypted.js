/*
 *     collective.app.encrypted is free software: you can redistribute it and/or modify
 *     it under the terms of the GNU General Public License as published by
 *     the Free Software Foundation, version 2 of the License.
 *              
 *     collective.app.encrypted is distributed in the hope that it will be useful,
 *     but WITHOUT ANY WARRANTY; without even the implied warranty of
 *     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *     GNU General Public License for more details.
 *
 *     You should have received a copy of the GNU General Public License
 *     along with plone.app.encrypted.  If not, see <http://www.gnu.org/licenses/>.
 */
var encrypted = {
  /** 
   * Makes sure the prerequisities for encrypting content are met. If they are the function will start the encryption process.
   * @param {String} pageType type of the page (add|edit) 
   */
  prepareForEncryption: function (pageType) {
    try {
      key = encrypted.getEncryptionKey(pageType);
      if (key!=null) {
        encrypted.encryptTextArea(pageType);
        encrypted.proceed(pageType);
        if (pageType === "edit") {
          // Working around 
          element = document.getElementById("form");
          element.setAttribute("onSubmit","return true"); 
          button = document.getElementById('form-buttons-save');
          button2 = button.cloneNode(true);
          button.parentElement.replaceChild(button2,button);
          button = document.getElementById('form-buttons-save');
          button.click();
        }
        return true; 
      }
    } catch (err) {
      alert("Unable to encrypt content: " + err.message);
    }
    return false;
  },
  /** 
   * Makes sure the prerequisities for decrypting content are met. If they are the function will start the decryption process.
   * @param {String} pageType type of the page (view|edit) 
   */
  prepareForDecryption: function (pageType) {
    try {
      key = encrypted.getEncryptionKey(pageType);
      if (key!=null) {
        encrypted.decryptTextArea(pageType);
        encrypted.proceed(pageType);
        return true;
      }
    } catch (err) {
      alert("Unable to decrypt content: " + err.message);
    }
    return false;
  },

  /** Decrypts encrypted textarea. Before calling this all the required keys should be found from session storage.
   *  @param {String} pageType type of the page (view|edit) 
   */
  decryptTextArea: function (pageType) {
    key = encrypted.getEncryptionKey(pageType);
    iv = encrypted.getIv(pageType);
    ciphertext = encrypted.getCipherText(pageType);
    plaintext = encrypted.decrypt(ciphertext, key, iv);
    encrypted.setPlainText(pageType, plaintext);
  },
  /**
   * Encrypts the textarea. Before calling this all the required keys should be found from session storage.
   * @param {String} pageType type of the page (edit|add)
   */
  encryptTextArea: function (pageType) {
    key = encrypted.getEncryptionKey(pageType);
    iv = encrypted.generateIv();
    plaintext = encrypted.getPlainText();
    ciphertext = encrypted.encrypt(plaintext, key, iv);
    encrypted.setCipherText(ciphertext);
  },
  /**
   * Manipulates the tinyMCE field by setting the text.
   * @param {String} ciphertext the hex encoded encrypted text string
   */  
  setCipherText: function (ciphertext) {
    editor = tinyMCE.get('form.widgets.encryptedcontent');
    if (editor==null) {
      element = document.getElementById("form.widgets.encryptedcontent");
      element.innerHTML = plaintext;
      element.value = plaintext;
    } else {
      tinyMCE.activeEditor.setContent(ciphertext);
      tinyMCE.triggerSave();
    }
  },
  /**  
   * Cleanup tasks after the encryption stuff has been done.
   * @param {String} pageType type of the page (add|edit|view)
   */
  proceed: function (pageType) {
    switch (pageType) {
    case "view": element = document.getElementById("encrypted-status"); 
                 element.className = "ok";
                 break;
    case "add":  element = document.getElementById("form");
                 element.setAttribute("onSubmit","return true"); 
                 // Plone adds to the submit button an event which will prevent the submitting by clicking the button again.
                 // The following code gets rid of that event.
                 button = document.getElementById('form-buttons-save');
                 button2 = button.cloneNode(true);
                 button.parentElement.replaceChild(button2,button);
                 button = document.getElementById('form-buttons-save');
                 button.click();
                 break;
    case "edit": element = document.getElementById("encrypted-status"); // This is for the decryption phase
                 element.className = "ok";
                 element = document.getElementById("form");
                 element.setAttribute("onSubmit","return encrypted.prepareForEncryption('edit')");
                 break;
    }
  },
  /**
   * Sets the text on page depending on the page.
   * @param {String} pageType type of the page (view|edit)
   * @paran {String} plaintext the text to be set
   */  
  setPlainText: function (pageType, plaintext) {
    switch (pageType) {
    case "view":
      element = document.getElementById("form-widgets-encryptedcontent");
      element.innerHTML = plaintext;
      element.style.visibility = "visible";
      break;
    case "edit": // Depending on the status of the page either one works
      element = document.getElementById("form.widgets.encryptedcontent");
      element.innerHTML = plaintext;
      editor = tinyMCE.get('form.widgets.encryptedcontent');
      if (editor!=null) editor.setContent(plaintext, {format : 'raw'});
      break;
    }
  },
  /** 
   * Decrypts data. sjcl throws somewhat well exceptions explaining what went wrong so there isn't much handling here.
   * @param {bitArray} ciphertext the encrypted data
   * @param {bitArray} key encryption key
   * @param {bitArray} iv initialization vector
   * @returns {String} plaintext
   */
  decrypt: function (ciphertext, key, iv) {
    var prp = new sjcl.cipher.aes(key);
    var plaintext = sjcl.mode.ccm.decrypt(prp, ciphertext, iv);
    return sjcl.codec.utf8String.fromBits(plaintext);
  },
  /** 
   * Encrypts data. sjcl throws somewhat well exceptions explaining what went wrong so there isn't much handling here.
   * @param {String} plaintext the text
   * @param {bitArray} key encryption key
   * @param {bitArray} iv initialization vector
   * @returns {bitArray} ciphertext
   */
  encrypt: function (plaintext, key, iv) {
    var prp = new sjcl.cipher.aes(key);
    var ciphertext = sjcl.mode.ccm.encrypt(prp, sjcl.codec.utf8String.toBits(plaintext), iv);
    return sjcl.codec.hex.fromBits(ciphertext);
  },
  /**
   * Returns the text from tinyMCE editor field.
   */ 
  getPlainText: function () {
    return tinyMCE.get('form.widgets.encryptedcontent').getContent();
  },
  /**
   * Returns the encrypted data from page.
   * @param {String} pageType type of the page (view|edit)
   */ 
  getCipherText: function (pageType) {
    var cipherText;
    switch (pageType) {
    case "view":
      content = document.getElementById("form-widgets-encryptedcontent").innerHTML;
      content = content.replace(/<p>|<\/p>/g, ''); // TinyMCE adds paragraphs, this is perhaps sane enough way to handle it.. Modifying TinyMCE probably wouldn't.
      cipherText = sjcl.codec.hex.toBits(content);
      break;
    case "edit":
      content = document.getElementById("form.widgets.encryptedcontent").value;
      content = content.replace(/<p>|<\/p>/g, '');
      cipherText = sjcl.codec.hex.toBits(content);
      break;
    }
    return cipherText;
  },
  /**
   * Builds and returns the encryption key. If not possible, will query the user and abort.
   * @param {String} pageType type of the page (view|edit|add)
   */ 
  getEncryptionKey: function (pageType) {
    var keyNames = [];
    var keys = {};
    var key;
    // Populate the array with requested keys
    requested = encrypted.getRequestedKeys(pageType);
    // Get keys from session storage and user
    keys = encrypted.getKeys(requested, pageType);
    if (!keys) { // Didn't get all the keys on this run
      return null;
    }
    // Build the final key
    key = encrypted.buildKey(keys);
    return key;
  },
  /** Returns an array consisting of the encryption keys.
   * @param {array} requested array of the requested keys (array of dicts)
   * @param {String} pageType type of the page (view|edit|add) 
   * @return {array} returns an array of dicts, containing keys. Will return null if not all keys were in session storage and had to pop up a dialog for them.
   */
  getKeys: function (requested, pageType) {
    var keys = requested;
    // Iterate through the array, and add the missing keys if they can be fetched from the session storage
    for (i in keys) {
      var keyFromSessionStorage;
      try {
        item = sessionStorage.getItem("encrypted_key_" + keys[i].UID);
        if (item) { // Something was found from the session storage, let's try attempt to handle it
          bits = sjcl.codec.hex.toBits(item);
          keys[i].key = bits;
        }
      } catch (err) {
        throw new Error("getKeys: Error with sessionStorage: " + err.message); // This is probably something major
      }
    }
    // Must query for missing keys?
    count = encrypted.queryForMissingKeys(keys, pageType);
    if (count > 0) return null; // We had to query for missing keys
    return keys;
  },
  /** Returns an array of the requested encryption keys. Items will be dictionaries.  
   * @param {String} pageType type of the page (view|add|edit)
   */
  getRequestedKeys: function (pageType) {
    var list = [];
    switch (pageType) {
    case "view":
      element = document.getElementById("encryptedtags-json");
      try {
        taglist = JSON.parse(element.innerHTML);
        for (i = 0; i < taglist.length; i++) {
          item = taglist[i];
          list.push(item);
        }
      } catch (err) {
        throw new Error("getRequestedKeys: Unable to parse json: " + err.message);
      }
      if (list.length == 0) throw new Error("getRequestedKeys: Unable to get requested keys, list stayed empty");
      break;
    case "edit":
    case "add":
      element = document.getElementById("form-widgets-encryptedtags-to");
      options = element.options;
      for (i = 0; i < options.length; i++) {
        list.push({
          "UID": options.item(i).value,
          "title": options.item(i).innerHTML
        });
      }
      if (list.length == 0) throw new Error("getRequestedKeys: Unable to get requested keys, list stayed empty");
      break;
    }
    return list;
  },
  /** 
   * Gets the initialization vector for AES from the page.
   * @param {String} pageType type of the page (view|edit)  
   */
  getIv: function (pageType) {
    var iv;
    element = document.getElementById("form-widgets-encryptediv");
    switch (pageType) {
    case "view":
      iv = element.innerHTML;
      break;
    case "edit":
      iv = element.value;
      break;
    }
    return sjcl.codec.hex.toBits(iv);
  },
  /**
   * Generates new initialization vector and saves it on form.
   */
  generateIv: function () {
    var iv = sjcl.codec.hex.fromBits(sjcl.random.randomWords(4));
    element = document.getElementById("form-widgets-encryptediv");
    if (!element) throw new Error("generateIv: unable to locate element");
    element.value = iv;
    return sjcl.codec.hex.toBits(iv);
  },
  /** 
   * Combines the keys into one final composite key.
   * @param {array} keys array consisting of the keys
   */
  buildKey: function (keys) {
    var encryptionKey;
    for (i in keys) {
      key = keys[i].key;
      // Check the type
      if (typeof key != "string") {
        key = sjcl.codec.hex.fromBits(key);
      }
      // First one we will just assign
      if (!encryptionKey) {
        encryptionKey = key;
      } else {
        // The others will be combined by bitwise XOR'ing
        encryptionKey = encrypted.xor(encryptionKey, key);
      }
    }
    return sjcl.codec.hex.toBits(encryptionKey);
  },
  /** 
   * Takes two objects and bitwise XORs them. This assumes similar length on input keys.
   * @param {String} one hex String
   * @param {String} two hex String
   * @returns {String} xorred String
   */
  xor: function (one, two) {
    var hex1 = one.toString();
    var hex2 = two.toString();
    var result = hex1;
    for (i = 0; i < hex1.length; i++) {
      num1 = parseInt(hex1[i], 16);
      num2 = parseInt(hex2[i], 16);
      xorred = num1 ^ num2;
      hexed = xorred.toString(16);
      result = result.substr(0, i) + hexed + result.substr(i + hexed.length);
    }
    return result;
  },
  /** Builds a query form for keys that could not be retrieved from session storage, and shows it. 
   * @return int how many keys where missing
   */
  queryForMissingKeys: function (keys, pageType) {
    button = document.getElementById("encrypted-save-keys-button");
    formlist = document.getElementById("encrypted_key_list");
    querydiv = document.getElementById("encrypted_key_query");
    if (!button || !element || !querydiv) throw new Error("queryForMissingKeys: unable to get elements: " + button + ":" + formlist + ":" + querydiv);
    count = 0; // How many keys were missing?
    // Clear the options from form
    if (formlist.hasChildNodes()) {
      while (formlist.childNodes.length >= 1) {
        formlist.removeChild(formlist.firstChild);
      }
    }
    // Add query for the missing keys
    for (i = 0; i < keys.length; i++) {
      item = keys[i];
      if (!item.key) {
        count++;
        var p = document.createElement("p");
        // Build label for query
        var label = document.createElement("label");
        label.setAttribute("for", item.UID);
        label.innerHTML = item.title;
        p.appendChild(label);
        // Build input field
        var input = document.createElement("input");
        input.setAttribute("id", item.UID);
        input.setAttribute("class", "fail");
        input.setAttribute("onInput", "encrypted.validateKeyInput(this)");
        input.setAttribute("type", "password");
        p.appendChild(input);
        formlist.appendChild(p);
      }
    }
    // Setup the continuation
    switch (pageType) {
    case "add":
      button.setAttribute("onClick", "encrypted.saveKeysFromForm();encrypted.prepareForEncryption('add');");
      break;
    case "view":
      button.setAttribute("onClick", "encrypted.saveKeysFromForm();encrypted.prepareForDecryption('view');");
      break;
    case "edit":
      if (document.getElementById("encrypted-status").className === "ok") {
       button.setAttribute("onClick", "encrypted.saveKeysFromForm();encrypted.prepareForEncryption('edit');");// We probably already have decrypted the page
      } else {
       button.setAttribute("onClick", "encrypted.saveKeysFromForm();encrypted.prepareForDecryption('edit');");
      }
      break;
    }
    // And show form if there are keys to be queried
    if (count > 0) {
      querydiv.style.display = "block";
    }
    return count;
  },
  /**
   * Validates one password input field.
   * @param {object} target the input field
   * @returns {boolean} result of the validation
   */ 
  validateKeyInput: function (target) {
    result = "fail";
    if (target && target.value && target.value.length > 5) {
      result = "ok";
    }
    target.className = result;
    encrypted.validateKeyInputForm();
  },
  /**
   * Goes through all the password input field, returns true if all them validated and false otherwise.
   * @returns {boolean} result of the validation
   */ 
  validateKeyInputForm: function () {
    result = true;
    elements = document.getElementById("encrypted_key_list").childNodes;
    for (i = 0; i < elements.length; i++) {
      element = elements[i];
      if (element.nodeName === "INPUT" && element.className === "fail") {
        result = false;
      }
    }
    button = document.getElementById("encrypted-save-keys-button");
    if (result) {
      button.disabled = false;
    } else {
      button.disabled = true;
    }
  },
  /**
   * Saves the keys from the key query form to session storage.
   */
  saveKeysFromForm: function () {
    // Go through the values and save the results to seassionStorage
    keylist = document.getElementById("encrypted_key_list").childNodes; // Array of <p>
    for (i = 0; i < keylist.length; i++) {
      paragraph = keylist[i].childNodes;
      for (k = 0; k < paragraph.length; k++) {
        element = paragraph[k];
        if (element.nodeName === "INPUT") {
          // This will help with the 00000 collision caused by two tags having same password and getting XOR'ed
          // Can't use (easily) a proper salt so this will not really bring more benefits offered by PBKDF2...
          var options = { salt : sjcl.codec.hex.toBits(element.id)};
          var result = sjcl.misc.cachedPbkdf2(element.value, options);
          var hash = result.key;
          //var hash = sjcl.hash.sha256.hash(element.value);
          sessionStorage.setItem("encrypted_key_" + element.id, sjcl.codec.hex.fromBits(hash));
        }
      }
    }
    // Hide the popup
    document.getElementById("encrypted_key_query").style.display = "none";
  }
};
